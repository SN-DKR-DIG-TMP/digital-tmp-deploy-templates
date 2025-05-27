import os
import argparse
import yaml
import csv
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input deployment YAML file')
    parser.add_argument('--csv', required=True, help='CSV file to update')
    parser.add_argument('--output', required=True, help='Output HTML file')
    parser.add_argument('--template', required=True, help='Jinja2 template file')
    parser.add_argument('--env', required=True, help='Environment name')
    parser.add_argument('--branch', required=True, help='Branch name')
    parser.add_argument('--version', required=True, help='Version from pom.xml')
    return parser.parse_args()

def load_deployments(yaml_path):
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
        projects = data.get('projects', [])
        keycloak_themes = data.get('keycloak_themes', [])
    return projects, keycloak_themes

def update_csv(csv_path, env, branch, version, projects, keycloak_themes):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_lines = []
    for proj in projects:
        mod_name = proj.get('name', 'unknown')
        image = proj.get('image', '')
        img_version = image.split(':')[-1] if ':' in image else version
        new_lines.append([now, mod_name, img_version, env, branch, version])

    for theme in keycloak_themes:
        image = theme.get('image', '')
        img_version = image.split(':')[-1] if ':' in image else version
        new_lines.append([now, theme['name'], img_version, env, branch, version])

    existing_lines = []
    if os.path.exists(csv_path):
        with open(csv_path, newline='') as f:
            reader = csv.reader(f)
            existing_lines = list(reader)[1:]  # skip header

    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Module', 'Version', 'Environment', 'Branch', 'Deployment_version'])
        writer.writerows(existing_lines + new_lines)

def read_csv(csv_path):
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

def get_last_deployments_per_env(rows):
    latest = {}
    for row in rows:
        env = row['Environment']
        date = row['Date']
        mod = row['Module']
        ver = row['Version']
        d_version = row['Deployment_version']
        if env not in latest or date > latest[env]['date']:
            latest[env] = {'date': date, 'modules': {mod: ver}}
        elif date == latest[env]['date']:
            latest[env]['modules'][mod] = ver
    return latest

def get_deployments_grouped_by_env(rows):
    envs = defaultdict(list)
    for row in rows:
        envs[row['Environment']].append(row)
    for env in envs:
        envs[env].sort(key=lambda r: r['Date'], reverse=True)
    return envs

def build_env_histories(envs):
    histories = {}
    for env, deployments in envs.items():
        modules = sorted(set(r['Module'] for r in deployments))
        date_map = defaultdict(dict)
        for r in deployments:
            date_map[r['Date']][r['Module']] = r['Version']

        formatted_rows = []
        for date in sorted(date_map.keys(), reverse=True):
            line = [date]
            for mod in modules:
                line.append(date_map[date].get(mod, ''))
            deployment_version = next((r['Deployment_version'] for r in deployments if r['Date'] == date), '')
            line.append(deployment_version)
            formatted_rows.append(line)

        histories[env] = {
            'modules': modules,
            'rows': formatted_rows
        }
    return histories

def main():
    args = parse_args()
    projects, keycloak_themes = load_deployments(args.input)
    update_csv(args.csv, args.env, args.branch, args.version, projects, keycloak_themes)
    rows = read_csv(args.csv)
    last_deployments = get_last_deployments_per_env(rows)
    all_deployments = get_deployments_grouped_by_env(rows)
    env_histories = build_env_histories(all_deployments)

    env = Environment(loader=FileSystemLoader(os.path.dirname(args.template)))
    template = env.get_template(os.path.basename(args.template))

    modules = sorted(set(row['Module'] for row in rows))
    env_names = sorted(last_deployments.keys())
    date_row = [last_deployments[env]['date'] for env in env_names]

    summary_rows = []
    for mod in modules:
        row = []
        for env in env_names:
            mod_ver = last_deployments.get(env, {}).get('modules', {}).get(mod, '')
            row.append(mod_ver)
        summary_rows.append((mod, row))

    html_content = template.render(
        last_deployments=last_deployments,
        all_deployments=all_deployments,
        env_names=env_names,
        date_row=date_row,
        summary_rows=summary_rows,
        env_histories=env_histories,
        modules=modules,
        deployment_version=args.version
    )

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == '__main__':
    main()

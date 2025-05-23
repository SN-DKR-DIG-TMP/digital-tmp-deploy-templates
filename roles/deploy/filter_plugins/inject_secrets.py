import copy
from typing import List, Dict, Any

def inject_secrets(modules: List[Dict], secrets_list: List[Dict]) -> List[Dict]:
    """
    Version ultra-robuste qui:
    - Préserve tous les caractères spéciaux
    - Gère les formats YAML complexes
    - Protège contre les erreurs d'interprétation
    """
    secrets_db = {}
    for secret in secrets_list:
        if isinstance(secret, dict) and 'name' in secret:
            secrets_db[secret['name']] = {
                k: str(v) if v is not None else ''  # Conversion string explicite
                for k, v in secret.items()
                if k != 'name'
            }

    processed_modules = []
    for module in copy.deepcopy(modules):
        if not isinstance(module, dict):
            continue

        module_name = module.get('name')
        if not module_name or module_name not in secrets_db:
            processed_modules.append(module)
            continue

        env = module.get('environment', {})
        for key, value in env.items():
            if isinstance(value, str) and value.startswith('%') and value.endswith('%'):
                secret_key = value[1:-1]
                if secret_key in secrets_db[module_name]:
                    env[key] = secrets_db[module_name][secret_key]

        processed_modules.append(module)

    return processed_modules

class FilterModule:
    def filters(self):
        return {'inject_secrets': inject_secrets}
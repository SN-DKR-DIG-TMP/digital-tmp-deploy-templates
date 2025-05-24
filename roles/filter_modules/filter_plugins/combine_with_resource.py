def combine_with_resource(project, resources):
    # Vérifie que project est bien un dict
    if not isinstance(project, dict):
        return project
    # Parcours toutes les ressources pour trouver une correspondance par "name"
    for resource in resources:
        if isinstance(resource, dict) and resource.get("name") == project.get("name"):
            # Fusionne resource dans project (resource écrase project en cas de conflit)
            merged = resource.copy()
            merged.update(project)
            return merged
    # Si aucune ressource ne correspond, retourne le project d'origine
    return project

class FilterModule(object):
    def filters(self):
        return {
            'combine_with_resource': combine_with_resource
        }

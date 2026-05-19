from django.apps import apps


def module_name_to_app_name(module_name: str) -> str | None:
    for app_config in apps.get_app_configs():
        if app_config.name in module_name:
            relative_module = module_name.replace(f"{app_config.name}.", "")
            return f"{app_config.label}.{relative_module}"

    return None

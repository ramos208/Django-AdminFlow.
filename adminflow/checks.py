"""
adminflow.checks
================
Django system checks for AdminFlow settings and app configuration.
"""

from __future__ import annotations

from django.conf import settings
from django.core.checks import Error, Tags, Warning, register


@register(Tags.templates, Tags.admin)
def check_adminflow_configuration(app_configs, **kwargs):
    errors = []

    # 1. Check INSTALLED_APPS order (adminflow before django.contrib.admin)
    installed = list(getattr(settings, "INSTALLED_APPS", []))
    adminflow_idx = None
    django_admin_idx = None
    for idx, entry in enumerate(installed):
        if entry == "adminflow" or entry.startswith("adminflow."):
            if adminflow_idx is None:
                adminflow_idx = idx
        elif entry == "django.contrib.admin":
            if django_admin_idx is None:
                django_admin_idx = idx
    if (
        adminflow_idx is not None
        and django_admin_idx is not None
        and adminflow_idx > django_admin_idx
    ):
        errors.append(
            Warning(
                "'adminflow' appears after 'django.contrib.admin' in INSTALLED_APPS.",
                hint="Place 'adminflow' before 'django.contrib.admin' in INSTALLED_APPS so AdminFlow templates override default admin templates.",
                id="adminflow.W001",
            )
        )

    # 2. Validate ADMINFLOW_NAVIGATION / ADMINFLOW_NAVIGATION_PROVIDER
    for setting_name in ("ADMINFLOW_NAVIGATION_PROVIDER", "ADMINFLOW_NAVIGATION"):
        if not hasattr(settings, setting_name):
            continue
        nav_cfg = getattr(settings, setting_name)
        if nav_cfg in (None, False, {}, [], ()):
            continue
        if callable(nav_cfg):
            continue
        if isinstance(nav_cfg, str):
            from django.utils.module_loading import import_string

            try:
                resolved = import_string(nav_cfg)
            except Exception as exc:
                errors.append(
                    Error(
                        f"{setting_name} could not be imported ({exc}).",
                        hint=f"Ensure {setting_name} is a valid dotted path to a callable or a list/dict of navigation groups.",
                        id="adminflow.E001",
                    )
                )
            else:
                if not callable(resolved):
                    errors.append(
                        Error(
                            f"{setting_name} dotted path '{nav_cfg}' did not resolve to a callable.",
                            hint=f"Point {setting_name} to a callable accepting (request, apps) or (request).",
                            id="adminflow.E001",
                        )
                    )
            continue

        if isinstance(nav_cfg, dict):
            groups = nav_cfg.get("groups")
            if not isinstance(groups, (list, tuple)):
                errors.append(
                    Error(
                        f"{setting_name} dictionary must contain a 'groups' list or tuple.",
                        hint="Use {'groups': [{'key': '...', 'label': '...', 'models': [...]}]} or a list of group dicts.",
                        id="adminflow.E001",
                    )
                )
                continue
        elif isinstance(nav_cfg, (list, tuple)):
            groups = nav_cfg
        else:
            errors.append(
                Error(
                    f"{setting_name} must be a callable, dotted path string, dict, or list/tuple of group dicts.",
                    id="adminflow.E001",
                )
            )
            continue

        for idx, group in enumerate(groups):
            if not isinstance(group, dict):
                errors.append(
                    Error(
                        f"{setting_name} group at index {idx} must be a dict.",
                        id="adminflow.E001",
                    )
                )
                continue
            if not (group.get("label") or group.get("name") or group.get("default")):
                errors.append(
                    Error(
                        f"{setting_name} group at index {idx} is missing a 'label' (or 'name').",
                        id="adminflow.E001",
                    )
                )

    # 3. Validate ADMINFLOW_MODEL_ICONS
    if hasattr(settings, "ADMINFLOW_MODEL_ICONS"):
        icons_cfg = getattr(settings, "ADMINFLOW_MODEL_ICONS")
        if icons_cfg is not None and not callable(icons_cfg):
            if not isinstance(icons_cfg, dict):
                errors.append(
                    Error(
                        "ADMINFLOW_MODEL_ICONS must be a dict mapping model/app names to icon strings, or a callable.",
                        id="adminflow.E002",
                    )
                )
            else:
                for k, v in icons_cfg.items():
                    if not isinstance(k, str) or not isinstance(v, str) or not v.strip():
                        errors.append(
                            Error(
                                f"ADMINFLOW_MODEL_ICONS entry {k!r}: {v!r} must map a string key to a non-empty string icon name.",
                                id="adminflow.E002",
                            )
                        )
                        break

    return errors


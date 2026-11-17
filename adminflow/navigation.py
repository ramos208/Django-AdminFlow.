"""
adminflow.navigation
====================
Generic, opt-in grouped sidebar navigation provider and validator for AdminFlow.

This module is presentation-only: model links are sourced exclusively from
Django Admin's permission-filtered ``admin.site.get_app_list(request)`` (plus
optional explicit links gated by server-side ``permission`` / ``visible`` checks).
Client-side hiding is never used as authorization.
"""

from __future__ import annotations

import inspect
from typing import Any
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib import admin
from django.urls import NoReverseMatch, reverse
from django.utils.text import slugify

ALLOWED_SCHEMES = {"", "http", "https"}
FORBIDDEN_SCHEMES = {"javascript", "data", "vbscript", "file", "blob"}


def is_safe_navigation_url(url: Any) -> bool:
    """
    Validate that a navigation URL uses a safe relative path or HTTP(S) scheme.
    Rejects protocol-relative URLs (``//example.com``), control characters, and
    executable schemes such as ``javascript:`` or ``data:``.
    """
    if not isinstance(url, str):
        return False
    cleaned = url.strip()
    if not cleaned:
        return False
    if any(ord(ch) < 32 or ch in ("\x7f", " ", "\t", "\n", "\r") for ch in cleaned):
        return False
    if cleaned.startswith("//") or cleaned.startswith("\\"):
        return False
    try:
        parsed = urlsplit(cleaned)
    except ValueError:
        return False
    scheme = (parsed.scheme or "").lower()
    if scheme in FORBIDDEN_SCHEMES or scheme not in ALLOWED_SCHEMES:
        return False
    if not scheme and not cleaned.startswith("/"):
        return False
    return True


def _resolve_callable(target: Any):
    if callable(target):
        return target
    if isinstance(target, str) and "." in target:
        from django.utils.module_loading import import_string

        return import_string(target)
    return None


def _check_visibility(spec: dict[str, Any], request: Any) -> bool:
    """Evaluate server-side visibility and permission rules for a group, section, or item."""
    user = getattr(request, "user", None) if request is not None else None

    if "visible" in spec:
        vis = spec["visible"]
        if callable(vis):
            try:
                if not bool(vis(request)):
                    return False
            except Exception:
                return False
        elif not bool(vis):
            return False

    perm = spec.get("permission") or spec.get("permissions")
    if perm:
        if user is None or not getattr(user, "is_authenticated", False):
            return False
        if isinstance(perm, str):
            if not user.has_perm(perm):
                return False
        elif isinstance(perm, (list, tuple, set)):
            if not user.has_perms(list(perm)):
                return False
        else:
            return False

    return True


def _is_url_active(request_path: str, item_url: str, index_url: str = "/admin/") -> bool:
    if not request_path or not item_url:
        return False
    if item_url == index_url or item_url.rstrip("/") == index_url.rstrip("/"):
        return request_path == item_url
    return request_path == item_url or request_path.startswith(item_url)


def _normalize_model_key(app_label: str, object_name: str) -> tuple[str, str]:
    app_clean = str(app_label or "").strip().lower()
    obj_clean = str(object_name or "").strip().lower()
    return f"{app_clean}.{obj_clean}", obj_clean


def _resolve_item_url(item: dict[str, Any]) -> str | None:
    raw_url = item.get("url") or item.get("admin_url")
    if not raw_url and item.get("url_name"):
        try:
            raw_url = reverse(item["url_name"], args=item.get("url_args"), kwargs=item.get("url_kwargs"))
        except (NoReverseMatch, TypeError, ValueError):
            return None
    if is_safe_navigation_url(raw_url):
        return str(raw_url).strip()
    return None


def _sanitize_normalized_groups(
    raw_groups: Any,
    request: Any,
    index_url: str = "/admin/",
) -> list[dict[str, Any]]:
    """
    Validate and normalize provider-returned group dictionaries into the stable
    AdminFlow navigation schema, enforcing server-side visibility and URL safety.
    """
    if not isinstance(raw_groups, (list, tuple)):
        return []

    request_path = getattr(request, "path", "") or ""
    normalized_groups: list[dict[str, Any]] = []

    for idx, raw_group in enumerate(raw_groups):
        if not isinstance(raw_group, dict):
            continue
        if not _check_visibility(raw_group, request):
            continue

        label = str(raw_group.get("label") or raw_group.get("name") or "").strip()
        if not label:
            continue
        key = str(raw_group.get("key") or slugify(label) or f"group-{idx}").strip()
        icon = str(raw_group.get("icon") or "folder").strip() or "folder"

        raw_sections = raw_group.get("sections")
        if raw_sections is None:
            top_items = raw_group.get("models") or raw_group.get("items") or []
            raw_sections = [{"label": "", "models": top_items}] if top_items else []

        if not isinstance(raw_sections, (list, tuple)):
            continue

        sections: list[dict[str, Any]] = []
        group_active = bool(raw_group.get("active", False))

        for sec_idx, raw_section in enumerate(raw_sections):
            if not isinstance(raw_section, dict):
                continue
            if not _check_visibility(raw_section, request):
                continue

            sec_label = str(raw_section.get("label") or raw_section.get("name") or "").strip()
            sec_key = str(
                raw_section.get("key")
                or (f"{key}-{slugify(sec_label)}" if sec_label else f"{key}-default-{sec_idx}")
            ).strip()

            raw_items = raw_section.get("models")
            if raw_items is None:
                raw_items = raw_section.get("items", [])
            if not isinstance(raw_items, (list, tuple)):
                continue

            items: list[dict[str, Any]] = []
            sec_active = bool(raw_section.get("active", False))

            for raw_item in raw_items:
                if not isinstance(raw_item, dict):
                    continue
                if not _check_visibility(raw_item, request):
                    continue

                item_url = _resolve_item_url(raw_item)
                if not item_url:
                    continue

                item_label = str(raw_item.get("label") or raw_item.get("name") or "").strip()
                if not item_label:
                    continue

                item_active = bool(raw_item.get("active", False)) or _is_url_active(
                    request_path, item_url, index_url=index_url
                )
                item_icon = raw_item.get("icon")
                normalized_item = {
                    "name": item_label,
                    "label": item_label,
                    "url": item_url,
                    "active": item_active,
                    "icon": str(item_icon).strip() if item_icon else None,
                    "object_name": raw_item.get("object_name"),
                }
                items.append(normalized_item)
                sec_active = sec_active or item_active

            if items:
                sections.append(
                    {
                        "key": sec_key,
                        "label": sec_label,
                        "active": sec_active,
                        "models": items,
                        "items": items,
                    }
                )
                group_active = group_active or sec_active

        if sections:
            flat_items = [item for sec in sections for item in sec["models"]]
            normalized_groups.append(
                {
                    "key": key,
                    "label": label,
                    "icon": icon,
                    "active": group_active,
                    "sections": sections,
                    "models": flat_items,
                    "items": flat_items,
                }
            )

    return normalized_groups


def _build_from_declarative_config(
    config: dict[str, Any] | list[Any] | tuple[Any, ...],
    request: Any,
    apps: list[dict[str, Any]],
    index_url: str = "/admin/",
) -> list[dict[str, Any]]:
    """
    Build grouped navigation from a declarative ``ADMINFLOW_NAVIGATION`` setting
    using only models already authorized in ``apps`` (plus any explicit ``items``
    that pass server-side permission/visibility checks).
    """
    if isinstance(config, dict):
        group_specs = config.get("groups", [])
        include_uncategorized = bool(config.get("include_uncategorized", False))
        uncategorized_label = str(config.get("uncategorized_label", "Other")).strip() or "Other"
        uncategorized_icon = str(config.get("uncategorized_icon", "grid_view")).strip() or "grid_view"
        uncategorized_key = str(config.get("uncategorized_key", "other")).strip() or "other"
    elif isinstance(config, (list, tuple)):
        group_specs = list(config)
        include_uncategorized = False
        uncategorized_label = "Other"
        uncategorized_icon = "grid_view"
        uncategorized_key = "other"
    else:
        return []

    if not isinstance(group_specs, (list, tuple)):
        return []

    hidden_models = {
        str(m).strip().lower()
        for m in getattr(
            settings,
            "ADMINFLOW_HIDDEN_MODELS",
            ("EmailDevice", "StaticDevice", "TOTPDevice"),
        )
    }

    # Index authorized models from `apps` in original order
    authorized_entries: list[dict[str, Any]] = []
    by_full_key: dict[str, dict[str, Any]] = {}
    by_obj_key: dict[str, list[dict[str, Any]]] = {}
    by_app_label: dict[str, list[dict[str, Any]]] = {}

    for app in apps or []:
        if not isinstance(app, dict):
            continue
        app_label = str(app.get("app_label") or "").strip()
        app_label_lower = app_label.lower()
        if app_label_lower in ("otp_email", "otp_static", "otp_totp"):
            continue
        for model in app.get("models") or []:
            if not isinstance(model, dict):
                continue
            obj_name = str(model.get("object_name") or model.get("name") or "").strip()
            if obj_name.lower() in hidden_models:
                continue
            admin_url = model.get("admin_url") or model.get("url")
            if not is_safe_navigation_url(admin_url):
                continue
            full_key, obj_key = _normalize_model_key(app_label, obj_name)
            entry = {
                "app_label": app_label,
                "app_label_lower": app_label_lower,
                "object_name": obj_name,
                "full_key": full_key,
                "obj_key": obj_key,
                "name": str(model.get("name") or obj_name).strip(),
                "url": str(admin_url).strip(),
                "icon": model.get("icon"),
                "model": model.get("model"),
            }
            authorized_entries.append(entry)
            by_full_key[full_key] = entry
            by_obj_key.setdefault(obj_key, []).append(entry)
            by_app_label.setdefault(app_label_lower, []).append(entry)

    consumed_ids: set[int] = set()

    def _claim_entries(
        selectors: Any = None,
        app_selectors: Any = None,
        label_overrides: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        claimed: list[dict[str, Any]] = []
        overrides_norm = {
            str(k).strip().lower(): str(v).strip()
            for k, v in (label_overrides or {}).items()
            if k and v
        }

        if isinstance(selectors, (list, tuple)):
            for sel in selectors:
                sel_key = str(sel or "").strip().lower()
                if not sel_key:
                    continue
                matches: list[dict[str, Any]] = []
                if "." in sel_key:
                    candidate = by_full_key.get(sel_key)
                    if candidate:
                        matches.append(candidate)
                else:
                    matches.extend(by_obj_key.get(sel_key, []))
                for match in matches:
                    if id(match) in consumed_ids:
                        continue
                    consumed_ids.add(id(match))
                    display_name = (
                        overrides_norm.get(match["full_key"])
                        or overrides_norm.get(match["obj_key"])
                        or match["name"]
                    )
                    claimed.append(
                        {
                            "name": display_name,
                            "label": display_name,
                            "url": match["url"],
                            "object_name": match["object_name"],
                            "icon": match.get("icon"),
                        }
                    )

        if isinstance(app_selectors, (list, tuple)):
            for app_sel in app_selectors:
                app_key = str(app_sel or "").strip().lower()
                for match in by_app_label.get(app_key, []):
                    if id(match) in consumed_ids:
                        continue
                    consumed_ids.add(id(match))
                    display_name = (
                        overrides_norm.get(match["full_key"])
                        or overrides_norm.get(match["obj_key"])
                        or match["name"]
                    )
                    claimed.append(
                        {
                            "name": display_name,
                            "label": display_name,
                            "url": match["url"],
                            "object_name": match["object_name"],
                            "icon": match.get("icon"),
                        }
                    )

        return claimed

    raw_groups: list[dict[str, Any]] = []
    default_group_spec: dict[str, Any] | None = None

    for spec in group_specs:
        if not isinstance(spec, dict):
            continue
        if not _check_visibility(spec, request):
            continue
        if spec.get("default"):
            default_group_spec = spec
            continue

        group_overrides = spec.get("model_labels") if isinstance(spec.get("model_labels"), dict) else {}
        sections_out: list[dict[str, Any]] = []

        # 1. Explicit sections inside group
        if isinstance(spec.get("sections"), (list, tuple)):
            for sec_spec in spec["sections"]:
                if not isinstance(sec_spec, dict):
                    continue
                if not _check_visibility(sec_spec, request):
                    continue
                sec_overrides = {
                    **group_overrides,
                    **(sec_spec.get("model_labels") if isinstance(sec_spec.get("model_labels"), dict) else {}),
                }
                sec_models = _claim_entries(
                    selectors=sec_spec.get("models"),
                    app_selectors=sec_spec.get("apps"),
                    label_overrides=sec_overrides,
                )
                extra_items = sec_spec.get("items") if isinstance(sec_spec.get("items"), (list, tuple)) else []
                sections_out.append(
                    {
                        "key": sec_spec.get("key"),
                        "label": sec_spec.get("label", ""),
                        "models": sec_models + list(extra_items),
                    }
                )

        # 2. Direct models / apps / items on the group
        direct_models = _claim_entries(
            selectors=spec.get("models"),
            app_selectors=spec.get("apps"),
            label_overrides=group_overrides,
        )
        direct_items = spec.get("items") if isinstance(spec.get("items"), (list, tuple)) else []
        if direct_models or direct_items:
            sections_out.insert(
                0,
                {
                    "label": "",
                    "models": direct_models + list(direct_items),
                },
            )

        raw_groups.append(
            {
                "key": spec.get("key"),
                "label": spec.get("label") or spec.get("name"),
                "icon": spec.get("icon", "folder"),
                "sections": sections_out,
            }
        )

    # Remaining authorized models go to `default: True` group or `include_uncategorized`
    remaining_entries = [e for e in authorized_entries if id(e) not in consumed_ids]
    if remaining_entries:
        if default_group_spec is not None:
            group_overrides = (
                default_group_spec.get("model_labels")
                if isinstance(default_group_spec.get("model_labels"), dict)
                else {}
            )
            overrides_norm = {
                str(k).strip().lower(): str(v).strip()
                for k, v in group_overrides.items()
                if k and v
            }
            rem_models = [
                {
                    "name": overrides_norm.get(e["full_key"])
                    or overrides_norm.get(e["obj_key"])
                    or e["name"],
                    "label": overrides_norm.get(e["full_key"])
                    or overrides_norm.get(e["obj_key"])
                    or e["name"],
                    "url": e["url"],
                    "object_name": e["object_name"],
                    "icon": e.get("icon"),
                }
                for e in remaining_entries
            ]
            extra_items = (
                default_group_spec.get("items")
                if isinstance(default_group_spec.get("items"), (list, tuple))
                else []
            )
            raw_groups.append(
                {
                    "key": default_group_spec.get("key", "other"),
                    "label": default_group_spec.get("label") or default_group_spec.get("name") or "Other",
                    "icon": default_group_spec.get("icon", "grid_view"),
                    "sections": [{"label": "", "models": rem_models + list(extra_items)}],
                }
            )
        elif include_uncategorized:
            rem_models = [
                {
                    "name": e["name"],
                    "label": e["name"],
                    "url": e["url"],
                    "object_name": e["object_name"],
                    "icon": e.get("icon"),
                }
                for e in remaining_entries
            ]
            raw_groups.append(
                {
                    "key": uncategorized_key,
                    "label": uncategorized_label,
                    "icon": uncategorized_icon,
                    "sections": [{"label": "", "models": rem_models}],
                }
            )

    return _sanitize_normalized_groups(raw_groups, request, index_url=index_url)


def get_navigation_config() -> Any:
    """Return the active navigation provider or declarative config if configured."""
    provider = getattr(settings, "ADMINFLOW_NAVIGATION_PROVIDER", None)
    if provider is not None:
        return provider
    return getattr(settings, "ADMINFLOW_NAVIGATION", None)


def is_grouped_navigation_enabled() -> bool:
    """Return True when a grouped navigation provider or config is enabled."""
    cfg = get_navigation_config()
    return bool(cfg)


def get_grouped_navigation(request: Any = None, apps: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """
    Resolve grouped sidebar navigation for ``request``.

    Returns an empty list when grouped navigation is disabled, when the user is
    unauthenticated (and no explicit ``apps`` list was supplied), or when no
    authorized items match.
    """
    config = get_navigation_config()
    if not config:
        return []

    user = getattr(request, "user", None) if request is not None else None
    if apps is None:
        if request is None or user is None or not getattr(user, "is_authenticated", False):
            return []
        try:
            apps = admin.site.get_app_list(request)
        except Exception:
            apps = []

    try:
        index_url = reverse("admin:index")
    except Exception:
        index_url = "/admin/"

    # 1. Callable or dotted import path provider
    provider_fn = None
    if callable(config) or isinstance(config, str):
        try:
            provider_fn = _resolve_callable(config)
        except Exception:
            return []
        if provider_fn is None:
            return []
        try:
            sig = inspect.signature(provider_fn)
            params = [
                p
                for p in sig.parameters.values()
                if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            has_varargs = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in sig.parameters.values())
            if len(params) >= 2 or has_varargs:
                raw_result = provider_fn(request, apps)
            elif len(params) == 1:
                raw_result = provider_fn(request)
            else:
                raw_result = provider_fn()
        except Exception:
            return []
        return _sanitize_normalized_groups(raw_result, request, index_url=index_url)

    # 2. Declarative dict/list configuration
    if isinstance(config, (dict, list, tuple)):
        return _build_from_declarative_config(config, request, apps, index_url=index_url)

    return []


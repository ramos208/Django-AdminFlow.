from django import forms
from django import template
from django.contrib import admin

register = template.Library()

def _get_widget_and_field(obj):
    """
    Safely extract (widget, form_field) from an AdminField, BoundField, forms.Field, or Widget.
    """
    if obj is None:
        return None, None
    if hasattr(obj, 'field') and not hasattr(obj, 'as_widget'):
        obj = obj.field
    if hasattr(obj, 'as_widget'):
        form_field = getattr(obj, 'field', None)
        widget = getattr(form_field, 'widget', None) or getattr(obj, 'widget', None)
        return widget, form_field
    if hasattr(obj, 'widget'):
        return obj.widget, obj
    if isinstance(obj, forms.Widget) or hasattr(obj, 'render'):
        return obj, None
    return obj, None

@register.filter(name='list_item')
def list_item(lst, index):
    """Return the item at the given index from a list."""
    try:
        return lst[int(index)]
    except (IndexError, TypeError, ValueError):
        return ''

@register.simple_tag(takes_context=True)
def get_admin_app_list(context):
    request = context.get('request')
    if not request:
        return []
    try:
        # Use default admin site
        return admin.site.get_app_list(request)
    except Exception:
        return []

@register.filter(name='zip_results')
def zip_results(results, cl):
    try:
        return zip(results, cl.result_list)
    except Exception:
        return zip(results, [])

@register.filter(name='add_class')
def add_class(value, arg):
    try:
        if hasattr(value, 'as_widget'):
            widget, _ = _get_widget_and_field(value)
            if widget and hasattr(widget, 'widgets'):
                for subwidget in widget.widgets:
                    css_classes = subwidget.attrs.get('class', '')
                    subwidget.attrs['class'] = f"{css_classes} {arg}".strip() if css_classes else arg
                return value.as_widget()
            else:
                existing = value.field.widget.attrs.get('class', '') if hasattr(value, 'field') and hasattr(value.field, 'widget') else ''
                css_classes = f"{existing} {arg}".strip() if existing else arg
                return value.as_widget(attrs={'class': css_classes})
        return value
    except Exception:
        return value

@register.filter(name='is_checkbox')
def is_checkbox(field):
    try:
        widget, form_field = _get_widget_and_field(field)
        if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
            return True
        if isinstance(form_field, (forms.BooleanField, forms.MultipleChoiceField)) and isinstance(widget, forms.CheckboxInput):
            return True
        widget_name = widget.__class__.__name__ if widget else ''
        return widget_name in ['CheckboxInput', 'CheckboxSelectMultiple', 'AdminCheckboxInput']
    except Exception:
        return False

@register.filter(name='is_readonly_password')
def is_readonly_password(field):
    try:
        widget, _ = _get_widget_and_field(field)
        widget_name = widget.__class__.__name__ if widget else ''
        return 'ReadOnlyPasswordHash' in widget_name or 'PasswordHash' in widget_name
    except Exception:
        return False

@register.filter(name='is_radio')
def is_radio(field):
    try:
        widget, _ = _get_widget_and_field(field)
        if isinstance(widget, (forms.RadioSelect,)):
            return True
        widget_name = widget.__class__.__name__ if widget else ''
        return 'Radio' in widget_name
    except Exception:
        return False

@register.filter(name='is_select')
def is_select(field):
    try:
        widget, _ = _get_widget_and_field(field)
        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            return True
        widget_name = widget.__class__.__name__ if widget else ''
        return widget_name in ['Select', 'SelectMultiple', 'AutocompleteSelect', 'AutocompleteSelectMultiple', 'Select2', 'NullBooleanSelect']
    except Exception:
        return False

@register.filter(name='is_json_field')
def is_json_field(field):
    try:
        widget, form_field = _get_widget_and_field(field)
        if isinstance(form_field, forms.JSONField):
            return True
        widget_name = widget.__class__.__name__ if widget else ''
        bf_name = str(getattr(field, 'name', '')).lower()
        if 'JSON' in widget_name or 'json' in bf_name:
            return True
        return False
    except Exception:
        return False

@register.filter(name='is_textarea')
def is_textarea(field):
    try:
        widget, _ = _get_widget_and_field(field)
        if isinstance(widget, forms.Textarea):
            return True
        widget_name = widget.__class__.__name__ if widget else ''
        return 'Textarea' in widget_name or widget_name in ['Textarea', 'AdminTextareaWidget']
    except Exception:
        return False

@register.filter(name='is_file')
def is_file(field):
    try:
        widget, _ = _get_widget_and_field(field)
        if isinstance(widget, (forms.FileInput, forms.ClearableFileInput)):
            return True
        widget_name = widget.__class__.__name__ if widget else ''
        return widget_name in ['ClearableFileInput', 'FileInput', 'AdminFileWidget']
    except Exception:
        return False

@register.filter(name='adminflow_icon')
def adminflow_icon(value):
    val_clean = str(value).lower().replace(' ', '').replace('_', '')
    
    # 1. Check if value is a model dict or Model class with ModelAdmin attribute
    if isinstance(value, dict):
        model_cls = value.get('model')
        model_name = value.get('object_name', str(value))
        if model_cls and model_cls in admin.site._registry:
            model_admin = admin.site._registry[model_cls]
            icon = getattr(model_admin, 'icon', None) or getattr(model_admin, 'admin_icon', None)
            if icon:
                return icon
        val_clean = str(model_name).lower().replace(' ', '').replace('_', '')
    elif hasattr(value, '_meta'):
        model_cls = value if isinstance(value, type) else value.__class__
        if model_cls in admin.site._registry:
            model_admin = admin.site._registry[model_cls]
            icon = getattr(model_admin, 'icon', None) or getattr(model_admin, 'admin_icon', None)
            if icon:
                return icon
        val_clean = str(model_cls._meta.object_name).lower().replace(' ', '').replace('_', '')

    # 2. Check custom user model icons from settings.py
    from django.conf import settings
    custom_icons = getattr(settings, 'ADMINFLOW_MODEL_ICONS', {})
    if custom_icons:
        for k, icon in custom_icons.items():
            if str(k).lower().replace(' ', '').replace('_', '') == val_clean:
                return icon

    # 3. Predefined smart model icon mapping
    icons = {
        'auth': 'security',
        'user': 'person',
        'users': 'group',
        'group': 'badge',
        'groups': 'folder_shared',
        'permission': 'verified_user',
        'permissions': 'verified_user',
        'userinformation': 'badge',
        'userinformations': 'badge',
        'site': 'public',
        'sites': 'language',
        'logentry': 'history',
        'logentries': 'history',
        'contenttype': 'layers',
        'contenttypes': 'category',
        'session': 'key',
        'sessions': 'lock',
        'customer': 'contact_mail',
        'customers': 'contact_mail',
        'order': 'shopping_cart',
        'orders': 'shopping_cart',
        'product': 'inventory_2',
        'products': 'inventory_2',
        'item': 'widgets',
        'items': 'widgets',
        'category': 'category',
        'categories': 'category',
        'tag': 'label',
        'tags': 'label',
        'setting': 'settings',
        'settings': 'settings',
        'notification': 'notifications',
        'notifications': 'notifications',
        'profile': 'account_circle',
        'profiles': 'account_circle',
        'file': 'description',
        'files': 'folder',
        'image': 'image',
        'images': 'photo_library',
        'crm': 'hub',
    }
    return icons.get(val_clean, 'grid_view')

@register.simple_tag
def get_user_stats():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        total = User.objects.count()
        active = User.objects.filter(is_active=True).count()
        inactive = User.objects.filter(is_active=False).count()
        staff = User.objects.filter(is_staff=True).count()
        superuser = User.objects.filter(is_superuser=True).count()
        return {
            'total': total,
            'active': active,
            'inactive': inactive,
            'staff': staff,
            'superuser': superuser,
        }
    except Exception:
        return {
            'total': 0,
            'active': 0,
            'inactive': 0,
            'staff': 0,
            'superuser': 0,
        }

@register.simple_tag
def get_system_stats():
    import django
    import sys
    from django.conf import settings
    from django.contrib import admin
    
    db_engine = "Unknown"
    db_name = "Unknown"
    try:
        db_config = settings.DATABASES['default']
        engine_path = db_config.get('ENGINE', '')
        db_engine = engine_path.split('.')[-1].replace('_', ' ').title()
        if 'sqlite' in engine_path:
            db_engine = 'SQLite'
        elif 'postgresql' in engine_path:
            db_engine = 'PostgreSQL'
        elif 'mysql' in engine_path:
            db_engine = 'MySQL'
        elif 'oracle' in engine_path:
            db_engine = 'Oracle'
        db_name = db_config.get('NAME', '')
        import os
        db_name = os.path.basename(db_name) if db_name else 'default'
    except Exception:
        pass
        
    app_count = 0
    model_count = 0
    model_names = ''
    try:
        model_count = len(admin.site._registry)
        distinct_apps = set(m._meta.app_label for m in admin.site._registry.keys())
        app_count = len(distinct_apps)
        model_names = '\n'.join(f'• {name}' for name in sorted(m._meta.verbose_name.title() for m in admin.site._registry.keys()))
    except Exception:
        pass
        
    django_ver = django.get_version()
    python_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    return {
        'db_engine': db_engine,
        'db_name': db_name,
        'model_count': model_count,
        'app_count': app_count,
        'model_names': model_names,
        'django_version': django_ver,
        'python_version': python_ver,
    }

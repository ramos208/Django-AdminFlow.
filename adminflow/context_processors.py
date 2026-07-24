from django.conf import settings
from django.templatetags.static import static

DEFAULTS = {
    'title': 'AdminFlow',
    'logo': None,
    'favicon': None,
    'company': 'AdminFlow',
    'sidebar_style': 'rounded',  # rounded, flat, sleek
    'theme': 'system',  # system, light, dark
    'density': 'comfortable',  # compact, comfortable
    'layout': 'default',
    'bg_color': '#f8f9ff',
    'sidebar_color': '#0f172a',
    'sidebar_text_color': '#94a3b8',
    'sidebar_active_text_color': '#ffffff',
    'navbar_color': '#ffffff',
    'primary_color': '#2563eb',
    'secondary_color': '#64748b',
    'success_color': '#22c55e',
    'warning_color': '#f59e0b',
    'danger_color': '#ef4444',
    'info_color': '#06b6d4',
    'border_radius': '16px',
    'font': 'Inter',
    'card_shadow': 'medium',
    'dark_mode': True,
    'compact_tables': True,
    'enable_glass_effect': False,
    'sidebar_collapsible': True,
    'sidebar_width': 280,
    'topbar_height': 64,
    'animation_speed': 'normal',
    'icon_pack': 'lucide',
    'table_density': 'comfortable',
    'date_format': 'MMM dd, yyyy',
    'time_format': '12h',
    'language': 'en',
    'rtl': False,
    'enable_command_palette': True,
    'enable_notifications': True,
    'enable_activity_log': True,
    'enable_audit_logs': True,
    'enable_global_search': True,
    'enable_quick_actions': True,
    'enable_multi_tab': True,
    'enable_theme_builder': True,
    'login_title': 'Master Your Enterprise Flow',
    'login_subtitle': 'A unified administrative engine built for scale, security, and developer productivity within the Django ecosystem.',
    'django_otp': False,
}

def adminflow_settings(request):
    context = {}
    for key, val in DEFAULTS.items():
        setting_name = f"ADMINFLOW_{key.upper()}"
        context[f"adminflow_{key}"] = getattr(settings, setting_name, val)

    # Automatically resolve logo URL:
    # 1) If user specified ADMINFLOW_LOGO:
    #    - If relative (e.g. 'logo.svg'), resolve against MEDIA_URL ('/media/logo.svg')
    #    - If absolute ('/static/...' or 'https://...'), use directly
    # 2) If ADMINFLOW_LOGO is not set (None), fall back to default package logo at static('adminflow/img/logo.svg')
    logo = context.get('adminflow_logo')
    if logo:
        if not (logo.startswith('/') or logo.startswith('http://') or logo.startswith('https://')):
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            context['adminflow_logo'] = f"{media_url.rstrip('/')}/{logo.lstrip('/')}"
    else:
        context['adminflow_logo'] = static('adminflow/img/logo.png')

    return context

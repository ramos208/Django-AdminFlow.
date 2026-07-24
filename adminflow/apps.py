from django.apps import AppConfig
from django.conf import settings

class AdminflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'adminflow'
    label = 'adminflow'

    def ready(self):
        # Pre-built Email OTP minimalist templates and subject defaults
        if not hasattr(settings, 'OTP_EMAIL_BODY_HTML_TEMPLATE_PATH'):
            setattr(settings, 'OTP_EMAIL_BODY_HTML_TEMPLATE_PATH', 'otp/email/token.html')
        if not hasattr(settings, 'OTP_EMAIL_BODY_TEMPLATE_PATH'):
            setattr(settings, 'OTP_EMAIL_BODY_TEMPLATE_PATH', 'otp/email/token.txt')
        app_title = getattr(settings, 'ADMINFLOW_TITLE', getattr(settings, 'ADMINFLOW_COMPANY', 'AdminFlow'))
        if not hasattr(settings, 'OTP_EMAIL_SUBJECT'):
            setattr(settings, 'OTP_EMAIL_SUBJECT', f'Your {app_title} Verification Code: {{token}}')

        if getattr(settings, 'ADMINFLOW_DJANGO_OTP', False):
            from django.contrib import admin
            from .views import adminflow_login_view
            admin.site.login = adminflow_login_view

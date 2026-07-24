from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class AdminFlowLoginForm(AuthenticationForm):
    username = forms.CharField(
        label=_("Username or Email"),
        widget=forms.TextInput(attrs={'autofocus': True, 'placeholder': 'Username or email address'})
    )

    def clean(self):
        username_input = self.cleaned_data.get('username', '').strip()
        password = self.cleaned_data.get('password')

        if username_input and password:
            # 1. Try exact username match
            self.user_cache = authenticate(self.request, username=username_input, password=password)

            # 2. Try case-insensitive username match
            if self.user_cache is None:
                user_by_username = User.objects.filter(username__iexact=username_input).first()
                if user_by_username:
                    self.user_cache = authenticate(self.request, username=user_by_username.get_username(), password=password)

            # 3. Try case-insensitive email match
            if self.user_cache is None:
                users_by_email = User.objects.filter(email__iexact=username_input)
                for u in users_by_email:
                    cached = authenticate(self.request, username=u.get_username(), password=password)
                    if cached:
                        self.user_cache = cached
                        break

            # 4. Detailed error check if user_cache is still None
            if self.user_cache is None:
                user_candidate = (
                    User.objects.filter(username__iexact=username_input).first() or
                    User.objects.filter(email__iexact=username_input).first()
                )
                if user_candidate and user_candidate.check_password(password):
                    if not user_candidate.is_active:
                        raise ValidationError(
                            _("This account is currently inactive. Please contact an administrator."),
                            code='inactive',
                        )
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

class AdminFlowOTPAuthenticationForm(AuthenticationForm):
    otp_token = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'placeholder': '123456 or Backup Code'})
    )

    def clean(self):
        cleaned_data = super().clean()
        user = self.get_user()

        from django.conf import settings
        if getattr(settings, 'ADMINFLOW_DJANGO_OTP', False) and user:
            try:
                import django_otp
                from django_otp import match_token

                if django_otp.user_has_device(user, confirmed=True):
                    otp_token = self.data.get('otp_token', '').strip()
                    if not otp_token:
                        raise ValidationError(
                            _("2FA Verification Required! Please enter your mobile app code, email code, or emergency backup code."),
                            code='otp_required'
                        )
                    device = match_token(user, otp_token)
                    if not device:
                        raise ValidationError(
                            _("Invalid 2FA Code or Emergency Backup Code. Please check your mobile authenticator app, email code, or 10 recovery codes."),
                            code='otp_invalid'
                        )
                    self.otp_device = device
            except ImportError:
                pass

        return cleaned_data

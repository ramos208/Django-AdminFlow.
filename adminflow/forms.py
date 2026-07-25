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
            username_field = getattr(User, 'USERNAME_FIELD', 'username')
            user_fields = [f.name for f in User._meta.get_fields()]
            has_username_attr = 'username' in user_fields
            has_email_attr = 'email' in user_fields

            # 1. Try standard authenticate with USERNAME_FIELD keyword arg
            auth_kwargs = {username_field: username_input, 'password': password}
            self.user_cache = authenticate(self.request, **auth_kwargs)

            # Fallback if custom backend expects 'username=' specifically
            if self.user_cache is None and username_field != 'username':
                self.user_cache = authenticate(self.request, username=username_input, password=password)

            # 2. Try case-insensitive lookup on USERNAME_FIELD
            if self.user_cache is None:
                filter_kwargs = {f"{username_field}__iexact": username_input}
                user_by_uname = User.objects.filter(**filter_kwargs).first()
                if user_by_uname:
                    auth_kwargs = {username_field: user_by_uname.get_username(), 'password': password}
                    self.user_cache = authenticate(self.request, **auth_kwargs)
                    if self.user_cache is None:
                        self.user_cache = authenticate(self.request, username=user_by_uname.get_username(), password=password)

            # 3. Try case-insensitive lookup on 'username' field (if field exists and != USERNAME_FIELD)
            if self.user_cache is None and has_username_attr and username_field != 'username':
                user_by_username = User.objects.filter(username__iexact=username_input).first()
                if user_by_username:
                    auth_kwargs = {username_field: user_by_username.get_username(), 'password': password}
                    self.user_cache = authenticate(self.request, **auth_kwargs)
                    if self.user_cache is None:
                        self.user_cache = authenticate(self.request, username=user_by_username.get_username(), password=password)

            # 4. Try case-insensitive lookup on 'email' field (if field exists and != USERNAME_FIELD)
            if self.user_cache is None and has_email_attr and username_field != 'email':
                users_by_email = User.objects.filter(email__iexact=username_input)
                for u in users_by_email:
                    auth_kwargs = {username_field: u.get_username(), 'password': password}
                    cached = authenticate(self.request, **auth_kwargs)
                    if cached is None:
                        cached = authenticate(self.request, username=u.get_username(), password=password)
                    if cached:
                        self.user_cache = cached
                        break

            # 5. Detailed error check if user_cache is still None
            if self.user_cache is None:
                user_candidate = None
                filter_kwargs = {f"{username_field}__iexact": username_input}
                user_candidate = User.objects.filter(**filter_kwargs).first()

                if not user_candidate and has_email_attr and username_field != 'email':
                    user_candidate = User.objects.filter(email__iexact=username_input).first()

                if not user_candidate and has_username_attr and username_field != 'username':
                    user_candidate = User.objects.filter(username__iexact=username_input).first()

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

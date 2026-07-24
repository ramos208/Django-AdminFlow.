"""
adminflow.user_admin
====================
Plug-and-play 2FA admin helpers for Django admin.

Usage in your admin.py::

    from adminflow.user_admin import AdminFlowUserAdminMixin, get_2fa_inlines
    from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

    @admin.register(User)
    class UserAdmin(AdminFlowUserAdminMixin, BaseUserAdmin):
        inlines = (YourCustomInline,) + get_2fa_inlines()
"""

import base64
import io
import json
import os

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils.safestring import mark_safe

User = get_user_model()

HAS_OTP_TOTP   = "django_otp.plugins.otp_totp"   in settings.INSTALLED_APPS
HAS_OTP_EMAIL  = "django_otp.plugins.otp_email"   in settings.INSTALLED_APPS
HAS_OTP_STATIC = "django_otp.plugins.otp_static"  in settings.INSTALLED_APPS

# ─────────────────────────────────────────────
# TOTP (Authenticator App) Inline
# ─────────────────────────────────────────────
if HAS_OTP_TOTP:
    from django_otp.plugins.otp_totp.models import TOTPDevice, default_key
    import qrcode

    AUTHENTICATOR_APP_CHOICES = [
        ("", "— Select Authenticator App —"),
        ("Google Authenticator", "Google Authenticator"),
        ("1Password", "1Password"),
        ("Authy", "Authy"),
        ("Microsoft Authenticator", "Microsoft Authenticator"),
        ("Bitwarden", "Bitwarden"),
        ("Duo Mobile", "Duo Mobile"),
        ("Aegis Authenticator", "Aegis Authenticator"),
        ("Raivo OTP", "Raivo OTP"),
        ("Keychain (iOS/macOS)", "Keychain (iOS/macOS)"),
        ("Other", "Other"),
    ]

    class TOTPDeviceForm(forms.ModelForm):
        key = forms.CharField(widget=forms.HiddenInput(), required=False)
        name = forms.ChoiceField(
            choices=AUTHENTICATOR_APP_CHOICES,
            label="Authenticator App",
            help_text="Select which authenticator app you are using. Each app must be unique per account.",
            widget=forms.Select(attrs={"style": "width:100%; max-width:320px;"}),
        )
        verification_code = forms.CharField(
            required=False, max_length=6, min_length=6,
            label="6-Digit Verification Code (from Mobile App)",
            widget=forms.TextInput(attrs={
                "placeholder": "123456",
                "style": "letter-spacing:2px;font-family:monospace;font-weight:bold;width:180px;text-align:center;font-size:14px;",
                "autocomplete": "off",
            }),
            help_text="Scan the QR code above with your authenticator app, enter the 6-digit code, then click Save.",
        )

        class Meta:
            model = TOTPDevice
            fields = ("name", "key", "confirmed")

        def _get_validation_exclusions(self):
            exclusions = super()._get_validation_exclusions()
            for f in ("name","key","step","t0","digits","tolerance","drift","last_t",
                      "throttling_failure_count","throttling_failure_timestamp"):
                exclusions.add(f)
            return exclusions

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if not self.instance.pk:
                k = getattr(self.instance, "key", None) or self.initial.get("key") or default_key()
                self.instance.key = k
                self.initial["key"] = k
                if "key" in self.fields:
                    self.fields["key"].initial = k

            if "name" in self.fields:
                user = getattr(self.instance, "user", None)
                used_names = set()
                if user and user.pk:
                    qs = TOTPDevice.objects.filter(user=user)
                    if self.instance.pk:
                        qs = qs.exclude(pk=self.instance.pk)
                    used_names = set(qs.values_list("name", flat=True))
                available = [
                    (val, label) for val, label in AUTHENTICATOR_APP_CHOICES
                    if val == "" or val not in used_names
                ]
                if self.instance.pk and self.instance.name:
                    existing = (self.instance.name, self.instance.name)
                    if existing not in available:
                        available.insert(1, existing)
                self.fields["name"].choices = available

        def has_changed(self):
            return True

        def clean(self):
            cleaned_data = super().clean()
            code = cleaned_data.get("verification_code", "").strip()
            submitted_key = (
                self.data.get(self.add_prefix("key"))
                or cleaned_data.get("key")
                or self.initial.get("key")
            )
            device_name = cleaned_data.get("name", "").strip()

            if submitted_key and not self.instance.pk:
                self.instance.key = submitted_key

            user = getattr(self.instance, "user", None) or cleaned_data.get("user")
            if not user:
                user_id = self.data.get(self.add_prefix("user"))
                if user_id:
                    user = User.objects.filter(pk=user_id).first()
            if user:
                self.instance.user = user

            if device_name and user and user.pk:
                qs = TOTPDevice.objects.filter(user=user, name=device_name)
                if self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    raise ValidationError({
                        "name": f"A 2FA device with '{device_name}' already exists for this account. "
                                "Please select a different authenticator app."
                    })

            cleaned_data["confirmed"] = False
            self.instance.confirmed = False
            self._is_verified = False

            if not code:
                raise ValidationError({
                    "verification_code": "Verification Code Required! Enter the 6-digit code from your authenticator app and click Save."
                })

            if hasattr(self.instance, "verify_token") and getattr(self.instance, "bin_key", None):
                self.instance.tolerance = 2
                if not self.instance.verify_token(code):
                    cleaned_data["confirmed"] = False
                    self.instance.confirmed = False
                    if self.instance.pk:
                        try:
                            self.instance.delete()
                        except Exception:
                            pass
                    raise ValidationError({
                        "verification_code": "Verification Failed! The code is invalid or expired. Re-scan the QR code and try again."
                    })
                cleaned_data["confirmed"] = True
                self.instance.confirmed = True
                self._is_verified = True
            else:
                if self.instance.pk:
                    try:
                        self.instance.delete()
                    except Exception:
                        pass
                raise ValidationError({"verification_code": "Verification Failed! Secret key is missing."})

            return cleaned_data

        def save(self, commit=True):
            instance = super().save(commit=False)
            if getattr(self, "_is_verified", False):
                instance.confirmed = True
            if commit:
                instance.save()
            return instance

    class TOTPDeviceInline(admin.StackedInline):
        model = TOTPDevice
        form = TOTPDeviceForm
        extra = 0
        max_num = 5
        fields = ("name", "key", "get_secret_key", "get_qrcode", "verification_code", "verification_status", "confirmed")
        readonly_fields = ("get_secret_key", "get_qrcode", "verification_status")
        verbose_name = "2FA Authenticator Device"
        verbose_name_plural = "2FA Authenticator Devices (OTP)"

        def get_formset(self, request, obj=None, **kwargs):
            self._parent_user = obj
            return super().get_formset(request, obj, **kwargs)

        def get_secret_key(self, obj):
            if not obj:
                return mark_safe("<span style='color:#64748b;font-size:12px;'>Secret key generated on first save.</span>")
            if not getattr(obj, "bin_key", None) and not getattr(obj, "key", None):
                obj.key = default_key()
            try:
                b32 = base64.b32encode(obj.bin_key).decode("utf-8")
                return format_html(
                    "<div><code style='font-size:14px;font-weight:bold;letter-spacing:2px;background:#f1f5f9;"
                    "padding:6px 10px;border-radius:8px;font-family:monospace;color:#0f172a;border:1px solid #cbd5e1;'>{}</code>"
                    "<span style='font-size:11px;color:#64748b;margin-left:10px;'>(Base32 — for Google Authenticator / 1Password)</span></div>",
                    b32,
                )
            except Exception:
                return "-"
        get_secret_key.short_description = "Secret Key (Base32)"

        def get_qrcode(self, obj):
            if not obj:
                return mark_safe("<span style='color:#64748b;font-size:12px;'>QR Code generated on first save.</span>")
            if not getattr(obj, "bin_key", None) and not getattr(obj, "key", None):
                obj.key = default_key()
            try:
                b32 = base64.b32encode(obj.bin_key).decode("utf-8")
                user = getattr(obj, "user", None) or getattr(self, "_parent_user", None)
                email = getattr(user, "email", None) if user else None
                username = user.get_username() if (user and hasattr(user, "get_username")) else None
                account_title = email or username or "User"
                app_title = getattr(settings, "ADMINFLOW_TITLE", getattr(settings, "ADMINFLOW_COMPANY", "AdminFlow"))
                config_url = f"otpauth://totp/{app_title}:{account_title}?secret={b32}&issuer={app_title}"
                img = qrcode.make(config_url)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                data = base64.b64encode(buf.getvalue()).decode("utf-8")
                return format_html(
                    "<div style='display:flex;align-items:center;gap:16px;margin-top:6px;'>"
                    "<img src='data:image/png;base64,{}' style='width:140px;height:140px;border-radius:12px;border:1px solid #cbd5e1;padding:6px;background:white;'/>"
                    "<div><p style='font-weight:700;font-size:13px;color:#0f172a;margin:0 0 2px;'>Scan with Authenticator App</p>"
                    "<p style='font-size:11px;color:#374151;font-family:monospace;background:#f1f5f9;display:inline-block;padding:2px 8px;border-radius:4px;margin:0 0 6px;'>{}: {}</p>"
                    "<p style='font-size:11px;color:#64748b;margin:0;max-width:260px;line-height:1.4;'>Scan this QR code, enter the 6-digit code below, then click Save to verify.</p>"
                    "</div></div>",
                    data, app_title, account_title,
                )
            except Exception as e:
                return format_html("<span style='color:#ef4444;font-size:11px;'>Error generating QR code: {}</span>", str(e))
        get_qrcode.short_description = "QR Code (Scan for Authenticator App)"

        def verification_status(self, obj):
            if not obj or not getattr(obj, "bin_key", None):
                return mark_safe("<span style='color:#64748b;font-size:12px;'>Save device to view status.</span>")
            if obj.confirmed:
                return mark_safe(
                    "<div style='display:inline-flex;align-items:center;gap:6px;background:#f0fdf4;"
                    "border:1px solid #bbf7d0;color:#166534;font-weight:700;font-size:12px;"
                    "padding:6px 14px;border-radius:8px;'>&#10003; 2FA Authenticator Device Verified &amp; Active</div>"
                )
            return mark_safe(
                "<div style='background:#fffbeb;border:1px solid #fde68a;padding:10px 14px;border-radius:8px;margin-top:4px;'>"
                "<p style='font-weight:700;font-size:12px;color:#b45309;margin:0 0 2px;'>&#9888;&#65039; Security Verification Pending</p>"
                "<p style='font-size:11px;color:#78350f;margin:0;'>Enter your 6-digit code above and click <b>Save</b> to verify &amp; activate 2FA.</p>"
                "</div>"
            )
        verification_status.short_description = "Security Verification"


# ─────────────────────────────────────────────
# Email OTP Inline
# ─────────────────────────────────────────────
if HAS_OTP_EMAIL:
    from django_otp.plugins.otp_email.models import EmailDevice

    class EmailDeviceForm(forms.ModelForm):
        class Meta:
            model = EmailDevice
            fields = ("confirmed",)

        def _get_validation_exclusions(self):
            exclusions = super()._get_validation_exclusions()
            exclusions.add("name")
            exclusions.add("email")
            return exclusions

        def has_changed(self):
            return True

        def clean(self):
            cleaned_data = super().clean()
            if self.instance and hasattr(self.instance, "user") and self.instance.user:
                self.instance.email = (
                    self.instance.user.email
                    or f"{self.instance.user.username}@example.com"
                )
            self.instance.name = "default"
            return cleaned_data

    class EmailDeviceInline(admin.StackedInline):
        model = EmailDevice
        form = EmailDeviceForm
        extra = 0
        max_num = 1
        fields = ("confirmed",)
        verbose_name = "Email OTP 2FA Device"
        verbose_name_plural = "Email OTP 2FA Devices (Email Verification Code)"


# ─────────────────────────────────────────────
# Static / Backup Codes Inline
# ─────────────────────────────────────────────
if HAS_OTP_STATIC:
    from django_otp.plugins.otp_static.models import StaticDevice, StaticToken

    def _get_backup_codes_file():
        base_dir = getattr(settings, "BASE_DIR", ".")
        return os.path.join(str(base_dir), ".adminflow_backup_codes.json")

    def _load_batch_tokens(device_id):
        filepath = _get_backup_codes_file()
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    return json.load(f).get(str(device_id), [])
            except Exception:
                pass
        return []

    def _save_batch_tokens(device_id, tokens):
        filepath = _get_backup_codes_file()
        data = {}
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data[str(device_id)] = tokens
        try:
            with open(filepath, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    class StaticDeviceForm(forms.ModelForm):
        class Meta:
            model = StaticDevice
            fields = ("confirmed",)

        def has_changed(self):
            return True

        def clean(self):
            cleaned_data = super().clean()
            self.instance.name = "backup_codes"
            self.instance.confirmed = True
            return cleaned_data

    class StaticDeviceInline(admin.StackedInline):
        model = StaticDevice
        form = StaticDeviceForm
        extra = 0
        max_num = 1
        fields = ("confirmed", "get_backup_codes")
        readonly_fields = ("get_backup_codes",)
        verbose_name = "10 Emergency Recovery Backup Codes"
        verbose_name_plural = "10 Emergency Recovery Backup Codes (Static OTP)"

        def get_backup_codes(self, obj):
            if not obj or not getattr(obj, "pk", None):
                return mark_safe(
                    "<span style='color:#64748b;font-size:12px;'>Click <b>Save</b> to generate 10 Emergency Recovery Backup Codes.</span>"
                )
            active_tokens = list(StaticToken.objects.filter(device=obj).values_list("token", flat=True))
            batch_tokens  = _load_batch_tokens(obj.pk)
            if not active_tokens:
                active_tokens = []
                for _ in range(10):
                    t = StaticToken.random_token()
                    StaticToken.objects.create(device=obj, token=t)
                    active_tokens.append(t)
                batch_tokens = list(active_tokens)
                _save_batch_tokens(obj.pk, batch_tokens)
                if not obj.confirmed:
                    obj.confirmed = True
                    obj.save()
            elif not batch_tokens:
                batch_tokens = list(active_tokens)
                _save_batch_tokens(obj.pk, batch_tokens)

            display = batch_tokens if batch_tokens else active_tokens
            lis = []
            for t in display:
                if t in active_tokens:
                    lis.append(
                        f"<li style='font-family:monospace;font-weight:bold;font-size:13px;background:#f1f5f9;"
                        f"padding:6px 10px;border-radius:8px;border:1px solid #cbd5e1;text-align:center;"
                        f"color:#0f172a;display:inline-flex;align-items:center;justify-content:center;' title='Active'>{t}</li>"
                    )
                else:
                    lis.append(
                        f"<li style='font-family:monospace;font-weight:bold;font-size:13px;background:#fef2f2;"
                        f"padding:6px 10px;border-radius:8px;border:1px dashed #fca5a5;text-align:center;"
                        f"color:#991b1b;text-decoration:line-through;opacity:0.65;display:inline-flex;"
                        f"align-items:center;justify-content:center;gap:4px;' title='Used'>"
                        f"<span>{t}</span>"
                        f"<span style='font-size:9px;font-family:sans-serif;text-decoration:none;background:#ef4444;"
                        f"color:white;padding:1px 4px;border-radius:4px;font-weight:bold;line-height:1;'>USED</span></li>"
                    )
            return format_html(
                "<div style='margin-top:4px;'>"
                "<p style='font-size:11px;color:#64748b;margin-bottom:8px;line-height:1.4;'>"
                "Keep these 10 one-time emergency recovery codes in a safe place. Each code can be used ONCE.</p>"
                "<ul style='display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));"
                "gap:8px;list-style:none;padding:0;margin:0 0 12px;'>{}</ul>"
                "<div style='display:flex;align-items:center;gap:16px;margin-top:8px;'>"
                "<a href='/admin/auth/user/{}/download-backup-codes/' "
                "style='background:#2563eb;color:white;font-weight:bold;font-size:11px;padding:6px 14px;"
                "border-radius:8px;text-decoration:none;display:inline-flex;align-items:center;gap:6px;'>"
                "&#128229; Download Backup Codes (.txt)</a>"
                "<a href='/admin/auth/user/{}/generate-backup-codes/' "
                "style='font-size:11px;color:#2563eb;font-weight:bold;text-decoration:underline;'>"
                "&#128260; Regenerate 10 New Codes</a>"
                "</div></div>",
                mark_safe("".join(lis)), obj.user_id, obj.user_id,
            )
        get_backup_codes.short_description = "10 One-Time Recovery Backup Codes"


# ─────────────────────────────────────────────
# Public helper: get available inline classes
# ─────────────────────────────────────────────
def get_2fa_inlines():
    """Return tuple of available 2FA inline classes based on installed OTP packages."""
    inlines = []
    if HAS_OTP_TOTP:
        inlines.append(TOTPDeviceInline)
    if HAS_OTP_EMAIL:
        inlines.append(EmailDeviceInline)
    if HAS_OTP_STATIC:
        inlines.append(StaticDeviceInline)
    return tuple(inlines)


# ─────────────────────────────────────────────
# AdminFlowUserAdminMixin
# ─────────────────────────────────────────────
class AdminFlowUserAdminMixin:
    """
    Mixin for Django UserAdmin that adds plug-and-play 2FA support.

    Usage::

        from adminflow.user_admin import AdminFlowUserAdminMixin, get_2fa_inlines

        @admin.register(User)
        class UserAdmin(AdminFlowUserAdminMixin, BaseUserAdmin):
            inlines = (YourInline,) + get_2fa_inlines()
    """

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            if HAS_OTP_TOTP and isinstance(instance, TOTPDevice):
                if any(getattr(f, "_is_verified", False) for f in formset.forms):
                    instance.confirmed = True
                if not instance.confirmed:
                    if instance.pk:
                        instance.delete()
                    TOTPDevice.objects.filter(user=instance.user, confirmed=False).delete()
                    continue
            elif HAS_OTP_EMAIL and isinstance(instance, EmailDevice):
                if hasattr(instance, "user") and instance.user:
                    instance.email = instance.user.email or f"{instance.user.username}@example.com"
                    instance.name = "default"
            elif HAS_OTP_STATIC and isinstance(instance, StaticDevice):
                instance.name = "backup_codes"
                instance.confirmed = True
                instance.save()
                if StaticToken.objects.filter(device=instance).count() == 0:
                    codes = []
                    for _ in range(10):
                        t = StaticToken.random_token()
                        StaticToken.objects.create(device=instance, token=t)
                        codes.append(t)
                    _save_batch_tokens(instance.pk, codes)
            instance.save()
        formset.save_m2m()

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = []
        if HAS_OTP_TOTP:
            custom.append(path(
                "<path:object_id>/verify-totp/<int:device_id>/",
                self.admin_site.admin_view(self.verify_totp_device_view),
                name="user_verify_totp",
            ))
        if HAS_OTP_EMAIL:
            custom.append(path(
                "<path:object_id>/send-email-otp/",
                self.admin_site.admin_view(self.send_email_otp_view),
                name="user_send_email_otp",
            ))
        if HAS_OTP_STATIC:
            custom.append(path(
                "<path:object_id>/generate-backup-codes/",
                self.admin_site.admin_view(self.generate_backup_codes_view),
                name="user_generate_backup_codes",
            ))
            custom.append(path(
                "<path:object_id>/download-backup-codes/",
                self.admin_site.admin_view(self.download_backup_codes_view),
                name="user_download_backup_codes",
            ))
        return custom + urls

    def download_backup_codes_view(self, request, object_id):
        from django.http import HttpResponse
        from django.shortcuts import get_object_or_404
        from django.utils import timezone
        user = get_object_or_404(User, pk=object_id)
        device, _ = StaticDevice.objects.get_or_create(
            user=user, name="backup_codes", defaults={"confirmed": True}
        )
        tokens = list(StaticToken.objects.filter(device=device).values_list("token", flat=True))
        if not tokens:
            tokens = []
            for _ in range(10):
                t = StaticToken.random_token()
                StaticToken.objects.create(device=device, token=t)
                tokens.append(t)
            device.confirmed = True
            device.save()
        app_title  = getattr(settings, "ADMINFLOW_TITLE", "AdminFlow")
        now_str    = timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        codes_txt  = "\n".join([f"  {i+1:2d}. {t}" for i, t in enumerate(tokens)])
        user_label = user.email or user.get_username()
        content = (
            f"=====================================================\n"
            f"         {app_title.upper()} 2FA EMERGENCY RECOVERY CODES\n"
            f"=====================================================\n"
            f" User Email   : {user_label}\n"
            f" Generated On : {now_str}\n"
            f"=====================================================\n\n"
            f" IMPORTANT: Keep these codes in a safe place.\n"
            f" Each code can be used ONCE to log in if you lose your phone.\n\n"
            f" RECOVERY CODES:\n"
            f" -----------------------------------------------------\n"
            f"{codes_txt}\n"
            f" -----------------------------------------------------\n\n"
            f"=====================================================\n"
        )
        response = HttpResponse(content, content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{user_label}_2fa_recovery_codes.txt"'
        return response

    def send_email_otp_view(self, request, object_id):
        from django.contrib import messages
        from django.shortcuts import get_object_or_404, redirect
        user = get_object_or_404(User, pk=object_id)
        device, _ = EmailDevice.objects.get_or_create(
            user=user, name="default",
            defaults={"confirmed": False, "email": user.email},
        )
        if not device.email:
            device.email = user.email
            device.save()
        device.generate_challenge()
        messages.success(
            request,
            f"Sent 6-digit verification code to {device.email}! Check your email, enter the code below, and click Save."
        )
        return redirect(request.META.get("HTTP_REFERER", f"/admin/auth/user/{object_id}/change/"))

    def generate_backup_codes_view(self, request, object_id):
        from django.contrib import messages
        from django.shortcuts import get_object_or_404, redirect
        user = get_object_or_404(User, pk=object_id)
        device, _ = StaticDevice.objects.get_or_create(
            user=user, name="backup_codes", defaults={"confirmed": True}
        )
        device.token_set.all().delete()
        codes = []
        for _ in range(10):
            token = StaticToken.random_token()
            device.token_set.create(token=token)
            codes.append(token)
        _save_batch_tokens(device.pk, codes)
        messages.success(
            request,
            f"Successfully generated 10 emergency recovery backup codes for {user.email or user.get_username()}."
        )
        return redirect(request.META.get("HTTP_REFERER", f"/admin/auth/user/{object_id}/change/"))

    def verify_totp_device_view(self, request, object_id, device_id):
        from django.contrib import messages
        from django.shortcuts import get_object_or_404, redirect
        device = get_object_or_404(TOTPDevice, pk=device_id, user_id=object_id)
        if request.method == "POST":
            code = request.POST.get("verify_code", "").strip()
            device.tolerance = 2
            if device.verify_token(code):
                device.confirmed = True
                device.save()
                messages.success(
                    request,
                    f"Verification Successful! 2FA Device '{device.name}' is now verified & active "
                    f"for {device.user.email or device.user.get_username()}."
                )
            else:
                messages.error(
                    request,
                    f"Verification Failed: '{code}' is not a valid code for '{device.name}'. "
                    "Check your device time sync and try again."
                )
        return redirect(request.META.get("HTTP_REFERER", f"/admin/auth/user/{object_id}/change/"))

    @admin.action(description="Enable 2FA (Create TOTP Device) for selected users")
    def enable_2fa_otp(self, request, queryset):
        if not HAS_OTP_TOTP:
            return
        count = 0
        for u in queryset:
            device, _ = TOTPDevice.objects.get_or_create(user=u, name="default", defaults={"confirmed": True})
            if not device.confirmed:
                device.confirmed = True
                device.save()
            count += 1
        self.message_user(request, f"Successfully enabled 2FA OTP for {count} user(s).")

    @admin.action(description="Generate 10 Emergency Backup Codes for selected users")
    def generate_10_backup_codes(self, request, queryset):
        if not HAS_OTP_STATIC:
            return
        count = 0
        for u in queryset:
            device, _ = StaticDevice.objects.get_or_create(user=u, name="backup_codes", defaults={"confirmed": True})
            device.token_set.all().delete()
            for _ in range(10):
                device.token_set.create(token=StaticToken.random_token())
            count += 1
        self.message_user(request, f"Successfully generated 10 emergency backup codes for {count} user(s).")


def unregister_otp_models():
    """Remove standalone OTP device models from the admin sidebar."""
    _models = []
    if HAS_OTP_TOTP:
        _models.append(TOTPDevice)
    if HAS_OTP_EMAIL:
        _models.append(EmailDevice)
    if HAS_OTP_STATIC:
        _models.append(StaticDevice)
    for m in _models:
        try:
            admin.site.unregister(m)
        except Exception:
            pass

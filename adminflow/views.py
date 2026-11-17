import time
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, get_user_model
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext as _
from django.conf import settings

# 15 minutes session duration for 2FA verification screen (in seconds)
OTP_SESSION_TIMEOUT_SECONDS = 900 

from .forms import AdminFlowLoginForm


def _admin_index_url():
    try:
        return reverse('admin:index')
    except Exception:
        return '/admin/'


def _admin_login_url():
    try:
        return reverse('admin:login')
    except Exception:
        return '/admin/login/'


def _user_display_label(user):
    if user is None:
        return ''
    email = getattr(user, 'email', None)
    if email:
        return str(email)
    if hasattr(user, 'get_full_name'):
        full_name = user.get_full_name()
        if full_name:
            return str(full_name)
    if hasattr(user, 'get_username'):
        return str(user.get_username())
    return str(user)


def adminflow_login_view(request, extra_context=None):
    default_next = _admin_index_url()
    if request.user.is_authenticated:
        return redirect(request.GET.get('next', default_next))

    reason = request.GET.get('reason')
    if reason == 'refreshed':
        # Clear 2FA session if user refreshed the verification page
        for key in ['pending_2fa_user_id', 'pending_2fa_next', 'pending_2fa_email', 'pending_2fa_created_at']:
            request.session.pop(key, None)
        messages.warning(request, "2FA verification was cancelled because the page was refreshed. Please log in again.")
    elif reason == 'expired':
        for key in ['pending_2fa_user_id', 'pending_2fa_next', 'pending_2fa_email', 'pending_2fa_created_at']:
            request.session.pop(key, None)
        messages.error(request, "Your 2FA verification session expired after 15 minutes. Please log in again.")

    if request.method == 'POST':
        form = AdminFlowLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Check 2FA requirement
            is_2fa_enabled = getattr(settings, 'ADMINFLOW_DJANGO_OTP', False)
            has_2fa_device = False
            
            if is_2fa_enabled:
                try:
                    import django_otp
                    has_2fa_device = django_otp.user_has_device(user, confirmed=True)
                except Exception:
                    has_2fa_device = False

            if not has_2fa_device:
                # Direct login to dashboard if no 2FA device configured
                auth_login(request, user)
                messages.success(request, f"🎉 Login Successful! Welcome back, {_user_display_label(user)}.")
                return redirect(request.GET.get('next', default_next))
            else:
                # 2FA is required -> store pending user id and timestamp in session
                request.session['pending_2fa_user_id'] = user.pk
                request.session['pending_2fa_next'] = request.GET.get('next', default_next)
                now_ts = time.time()
                request.session['pending_2fa_created_at'] = now_ts
                request.session['pending_2fa_last_sent_at'] = now_ts
                
                # Check if Email OTP is active -> send code first!
                try:
                    from django_otp.plugins.otp_email.models import EmailDevice
                    email_device = EmailDevice.objects.filter(user=user, confirmed=True).first()
                    if email_device:
                        app_title = getattr(settings, 'ADMINFLOW_TITLE', getattr(settings, 'ADMINFLOW_COMPANY', 'AdminFlow'))
                        app_company = getattr(settings, 'ADMINFLOW_COMPANY', getattr(settings, 'ADMINFLOW_TITLE', 'AdminFlow'))
                        email_device.generate_challenge(extra_context={
                            'user': user,
                            'adminflow_title': app_title,
                            'adminflow_company': app_company,
                        })
                        request.session['pending_2fa_email'] = email_device.email
                except Exception:
                    pass

                return redirect('adminflow_verify_2fa')
    else:
        form = AdminFlowLoginForm(request)

    context = {
        'form': form,
        'next': request.GET.get('next', default_next),
        'title': _('Log in'),
    }
    if extra_context:
        context.update(extra_context)
        
    return render(request, 'admin/login.html', context)

def adminflow_verify_2fa_view(request):
    User = get_user_model()
    user_id = request.session.get('pending_2fa_user_id')
    created_at = request.session.get('pending_2fa_created_at')
    login_url = _admin_login_url()

    # Check 15-minute 2FA session expiration
    if not user_id or not created_at or (time.time() - created_at > OTP_SESSION_TIMEOUT_SECONDS):
        for key in ['pending_2fa_user_id', 'pending_2fa_next', 'pending_2fa_email', 'pending_2fa_created_at', 'pending_2fa_last_sent_at']:
            request.session.pop(key, None)
        if user_id:
            messages.error(request, "Your 2FA verification session expired after 15 minutes. Please log in again.")
        return redirect(login_url)

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        for key in ['pending_2fa_user_id', 'pending_2fa_next', 'pending_2fa_email', 'pending_2fa_created_at', 'pending_2fa_last_sent_at']:
            request.session.pop(key, None)
        return redirect(login_url)

    next_url = request.session.get('pending_2fa_next', _admin_index_url())
    sent_email = request.session.get('pending_2fa_email')
    elapsed = time.time() - created_at
    remaining_seconds = max(0, int(OTP_SESSION_TIMEOUT_SECONDS - elapsed))

    last_sent_at = request.session.get('pending_2fa_last_sent_at', created_at)
    resend_cooldown_remaining = max(0, int(60 - (time.time() - last_sent_at)))

    if request.method == 'POST':
        # Resend email action
        if 'resend_email' in request.POST:
            try:
                from django_otp.plugins.otp_email.models import EmailDevice
                email_device = EmailDevice.objects.filter(user=user, confirmed=True).first()
                if email_device:
                    app_title = getattr(settings, 'ADMINFLOW_TITLE', getattr(settings, 'ADMINFLOW_COMPANY', 'AdminFlow'))
                    app_company = getattr(settings, 'ADMINFLOW_COMPANY', getattr(settings, 'ADMINFLOW_TITLE', 'AdminFlow'))
                    res = email_device.generate_challenge(extra_context={
                        'user': user,
                        'adminflow_title': app_title,
                        'adminflow_company': app_company,
                    })
                    request.session['pending_2fa_email'] = email_device.email
                    request.session['pending_2fa_last_sent_at'] = time.time()
                    if isinstance(res, str) and ("cooldown" in res.lower() or "not allowed" in res.lower()):
                        messages.warning(request, f"⏳ {res}")
                    else:
                        messages.success(request, f"📧 Sent new 6-digit code to {email_device.email}!")
                else:
                    messages.error(request, "No confirmed Email OTP device found for this account.")
            except Exception as e:
                messages.error(request, f"Error sending email verification code: {str(e)}")
            return redirect('adminflow_verify_2fa')

        otp_token = request.POST.get('otp_token', '').strip()
        if not otp_token:
            messages.error(request, "Please enter your 6-digit verification code or emergency backup code.")
        else:
            try:
                from django_otp import match_token
                device = match_token(user, otp_token)
                if device:
                    auth_login(request, user)
                    for key in ['pending_2fa_user_id', 'pending_2fa_next', 'pending_2fa_email', 'pending_2fa_created_at', 'pending_2fa_last_sent_at']:
                        request.session.pop(key, None)
                    messages.success(request, f"🔐 2FA Verification Successful! Welcome back, {_user_display_label(user)}.")
                    return redirect(next_url)
                else:
                    messages.error(request, "Invalid 2FA Verification Code or Emergency Backup Code. Please try again.")
            except Exception as e:
                messages.error(request, f"Authentication error: {str(e)}")

    user_email = getattr(user, 'email', None)
    has_totp_device = False
    has_email_device = False
    has_static_device = False
    try:
        from django_otp.plugins.otp_totp.models import TOTPDevice
        has_totp_device = TOTPDevice.objects.filter(user=user).exists()
    except Exception:
        pass
    try:
        from django_otp.plugins.otp_email.models import EmailDevice
        email_dev = EmailDevice.objects.filter(user=user).first()
        if email_dev:
            has_email_device = True
            sent_email = sent_email or email_dev.email or user_email
            if not email_dev.confirmed:
                email_dev.confirmed = True
                email_dev.save()
        elif user_email:
            has_email_device = True
            sent_email = sent_email or user_email
            email_dev, _ = EmailDevice.objects.get_or_create(user=user, name='default', defaults={'confirmed': True, 'email': user_email})
            if not email_dev.confirmed:
                email_dev.confirmed = True
                email_dev.save()
    except Exception:
        pass
    try:
        from django_otp.plugins.otp_static.models import StaticDevice
        has_static_device = StaticDevice.objects.filter(user=user).exists()
    except Exception:
        pass

    confirmed_count = sum([1 for x in [has_totp_device, has_email_device, has_static_device] if x])

    context = {
        'user': user,
        'sent_email': sent_email,
        'next': next_url,
        'remaining_seconds': remaining_seconds,
        'resend_cooldown_remaining': resend_cooldown_remaining,
        'has_totp_device': has_totp_device,
        'has_email_device': has_email_device,
        'has_static_device': has_static_device,
        'confirmed_count': confirmed_count,
    }
    return render(request, 'admin/verify_2fa.html', context)


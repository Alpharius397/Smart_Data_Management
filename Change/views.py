from typing import Literal
from django.urls import reverse
from django.shortcuts import render  # type: ignore
from django.http import HttpRequest, HttpResponse  # type: ignore
from User.errors import EmailAlreadyExists, OTPWrong, UserNameAlreadyExists
from Change.forms import ForgotEmail, UsernameChange, PasswordChange, EmailChange
from User.models import User, get_user, is_manager, is_admin
from tools.url_auth import auth_needed, get_user_from_session, htmx_response, is_auth_get, is_auth_get, is_hx_get, is_hx_post, is_hx_put, login_needed, read_body_as_form, set_otp_response
from constants import EMAIL_KEY, OTP_KEY, OTP_MESSAGE, OTP_SUBJECT, SUCCESS, SUCCESS_MESSAGE, SUCCESS_SUBJECT, WARNING, DEFAULT_ERROR
from tools.utils import setSwalAlert
from tools.mails import email_send, send_mail
from django.contrib.auth import logout
from Main.settings import settingsInterface as settings

############ UTILS ############
def send_success_mail(req: HttpRequest, type: Literal['username', 'email', 'password']):
    user = get_user(req)
    return email_send(SUCCESS_SUBJECT.format(type.capitalize()), user.email, SUCCESS_MESSAGE.format(type.capitalize().capitalize()))

############ HTTP Request ############
@login_needed()
@set_otp_response
def username_form(req: HttpRequest):
    if is_auth_get(req):
        return render(req, "Change/HTML/username.html", context={'form': UsernameChange()})

@login_needed()
@set_otp_response
def email_form(req: HttpRequest):
    if is_auth_get(req):
        return render(req, "Change/HTML/email.html", context={'form': EmailChange()})

@get_user_from_session
@login_needed()
@set_otp_response
def password_form(req: HttpRequest):
    if is_auth_get(req):
        return render(req, "Change/HTML/password.html", context={'form': PasswordChange()})
    
@htmx_response
@auth_needed()
def htmx_username_form(req: HttpRequest):
    
    if is_hx_post(req):
        context = setSwalAlert(title="Username Change")
        f = UsernameChange(req.POST)
        
        if f.is_valid():
            try:
                username = f.cleaned_data.get("Username")
                otp = f.cleaned_data.get("OTP")
                
                if User.objects.filter(username=username).exists():
                    raise UserNameAlreadyExists(username)
                
                OTP = req.session.get(OTP_KEY)
                
                if (not (OTP and (OTP == otp))):
                    raise OTPWrong()
                
                user = get_user(req)
                
                user.username = username
                user.save()
                
                setSwalAlert(context, "Username was changed successfully", 'success')
                send_success_mail(req, 'username')
                context['redirect'] = req.build_absolute_uri(reverse('User:index'))
                logout(req)
                
            except OTPWrong as e:
                setSwalAlert(context, e.get_error())
                
            except UserNameAlreadyExists as f:
                setSwalAlert(context, f.get_error())
                
            except Exception as e:
                setSwalAlert(context, DEFAULT_ERROR)
            
        else:
            setSwalAlert(context, f.getErrors())

            
        return render(req, "Change/HTMX/messages.html", context=context)

@htmx_response
@auth_needed()
def htmx_email_form(req: HttpRequest):
    
    if is_hx_post(req):
        context = setSwalAlert(title="Email Change")
        f = EmailChange(req.POST)
        
        if f.is_valid():
            try:
                email = f.cleaned_data.get("Email")
                otp = f.cleaned_data.get("OTP")
                
                if User.objects.filter(email=email).exists():
                    raise EmailAlreadyExists(email)
                
                OTP = req.session.get(OTP_KEY)
                
                if (not (OTP and (OTP == otp))):
                    raise OTPWrong()
                
                user = get_user(req)
                
                user.email = email
                user.save()
                setSwalAlert(context, "Email was changed successfully", 'success')
                send_success_mail(req, 'email')
                
                context['redirect'] = req.build_absolute_uri(reverse('User:index'))
                logout(req)
                
            except OTPWrong as e:
                setSwalAlert(context, e.get_error())
                
            except EmailAlreadyExists as f:
                setSwalAlert(context, f.get_error())
                
            except Exception as e:
                setSwalAlert(context, DEFAULT_ERROR)
            
        else:
            setSwalAlert(context, f.getErrors())

            
        return render(req, "Change/HTMX/messages.html", context=context)
    
@htmx_response
@get_user_from_session
@auth_needed()
def htmx_password_form(req: HttpRequest):
    
    if is_hx_post(req):
        context = setSwalAlert(title="Password Change")
        f = PasswordChange(req.POST)
        
        if f.is_valid():
            try:
                password = f.cleaned_data.get("Password")
                otp = f.cleaned_data.get("OTP")
                
                OTP = req.session.get(OTP_KEY)
                
                if (not (OTP and (OTP == otp))):
                    raise OTPWrong()
                
                user = get_user(req)
                
                user.set_password(password)
                user.save()
                setSwalAlert(context, "Password was changed successfully", 'success')
                send_success_mail(req, 'password')
                
                context['redirect'] = req.build_absolute_uri(reverse('User:index'))
                logout(req)
                
            except OTPWrong as e:
                setSwalAlert(context, e.get_error())
                
            except Exception as e:
                setSwalAlert(context, DEFAULT_ERROR)
            
        else:
            setSwalAlert(context, f.getErrors())
            
        return render(req, "Change/HTMX/messages.html", context=context)
    
@htmx_response
@get_user_from_session
@auth_needed()
def send_otp_mail(req: HttpRequest, type: Literal['username', 'email', 'password']):
    if is_hx_post(req):
        context = setSwalAlert(title="OTP Mail")
        otp = req.session.get(OTP_KEY, None)
        user = get_user(req)
        
        send_ok = False
        
        if otp:
            send_ok = email_send(OTP_SUBJECT.format(type.capitalize()), user.email, OTP_MESSAGE.format(type.capitalize(), otp))

        if send_ok:
            setSwalAlert(context, 'OTP has been send to your email', 'success')
        else:
            setSwalAlert(context, "Failed to send email. Please try again!")
        
        return render(req, "Change/HTMX/messages.html", context=context)
    
def forgot_password(req: HttpRequest):
    if(req.method == "GET"):
        return render(req, "Change/HTML/forgot.password.html", context={'form': ForgotEmail()})

@htmx_response
@read_body_as_form
def send_otp_mail_password(req: HttpRequest):
    if is_hx_post(req):
        context = setSwalAlert(title="OTP Mail")
        otp = req.session.get(OTP_KEY)
        user = get_user(req)
        
        send_ok = False
        
        if otp:
            send_ok = email_send(OTP_SUBJECT.format('Password'), user.email, OTP_MESSAGE.format('Password', otp))

        if send_ok:
            setSwalAlert(context, 'OTP has been send to your email', 'success')
        else:
            setSwalAlert(context, "Failed to send email. Please try again!")
        
        return render(req, "Change/HTMX/messages.html", context=context)
    
    elif is_hx_put(req):
        context = setSwalAlert(title="Email Status")
        
        f = ForgotEmail(req.PUT)
        
        if f.is_valid():
            try:
                email = f.cleaned_data.get("Email")
                
                user = User.objects.get(email=email)
                
                req.session[EMAIL_KEY] = user.email
                context['redirect'] = req.build_absolute_uri(reverse("Change:passChange"))
                
                setSwalAlert(text="Email was found!", icon='success')
                
            except User.DoesNotExist:
                setSwalAlert(context, text="Email is not registered")
                
            except Exception as e:
                print(e)
                setSwalAlert(context, DEFAULT_ERROR)
                
        else:
            setSwalAlert(context, text=f.getErrors())
            
        return render(req, "Change/HTMX/messages.html", context=context)

from User.errors import EmailAlreadyExists, OTPWrong, UserNameAlreadyExists
from django.http import HttpRequest, JsonResponse  # type: ignore
from Logs.loggers import APP_LOG, LogStructure, LogType
from Register.errors import UserExists
from University.models import Branch
from constants import DEFAULT_ERROR, MAX_RECORD
from Mobile.models import razorPayment
from tools.typesCauseWhyNot import NullStr
from tools.url_auth import (
    AccessPayLoad,
    RefreshPayLoad,
    getRequestToken,
    is_auth_get_student,
    is_auth_post_student,
    jwt_required,
    read_body_as_json,
    student_auth_needed,
)
from django.db.models import Q  # type: ignore
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from django.db import transaction  # type: ignore
from User.models import User, Role, RoleType, get_user, is_student
from Card.models import Card
from tools.url_auth import check_otp_response, set_otp_response
from Mobile.types import UserInfoResponse, LoginResponse, RegisterResponse, SubscriberResponse, CardResponse
from Change.forms import UsernameChange, PasswordChange, EmailChange

@csrf_exempt
@read_body_as_json
def mobile_login(req: HttpRequest):
    if req.method == "POST":
        response = LoginResponse(status=False, error=None, access=None, refresh=None)
        status: int = 500

        try:
            username = str(req.POST.get("user"))
            password = str(req.POST.get("password"))
            user = User.objects.get(username=username)

            if is_student(user) and user.check_password(password):
                response["access"] = AccessPayLoad(user).getToken()
                response["refresh"] = RefreshPayLoad(user).getToken()
                response["status"] = True
                status = 200

            else:
                response["error"] = "Incorrect Credentials"
                status = 403

        except User.DoesNotExist:
            status = 401
            response["error"] = "Invalid credentials"

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            response["error"] = DEFAULT_ERROR

        return JsonResponse(data=response, safe=False, status=status)


@csrf_exempt
@read_body_as_json
def mobile_register(req: HttpRequest):
    if req.method == "POST":
        response = RegisterResponse(access=None, refresh=None, status=False, error=None)
        status = 500
        f = RegisterForm(req.POST)

        try:
            with transaction.atomic():
                if f.is_valid():
                    user = f.cleaned_data.get("username", "")
                    email = f.cleaned_data.get("email", "")
                    password = f.cleaned_data.get("password", "")
                    branch = f.cleaned_data.get("branch", "")

                    exists = User.objects.filter(
                        Q(username=user) | Q(email=email)
                    ).exists()

                    if exists:
                        raise UserExists()

                    branchID = Branch.objects.get(id=branch)

                    user = User.objects.create_user(
                        user, email, password, is_active=False
                    )
                    role = Role(
                        user=user, belongs=branchID, role=RoleType.STUDENT.value
                    )
                    role.save()
                    response["status"] = True
                    status = 200
                else:
                    response["error"] = f.getErrors()

        except UserExists as f:
            status = 403
            response["error"] = "Username or Email is already registered!"

        except Branch.DoesNotExist:
            status = 401
            response["error"] = "Branch was not found!"

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            status = 500
            response["error"] = DEFAULT_ERROR

        return JsonResponse(data=response, safe=False, status=status)


@csrf_exempt
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
def subscriber_check(req: HttpRequest):
    response = SubscriberResponse(
        status=False, error=None, **getRequestToken(req)
    )

    status = 500

    if is_auth_get_student(req):  # Check if user has paid money
        try:
            cardID = req.GET.get("cardID")
            paymentDone = razorPayment.objects.filter(
                Q(user=req.user) | Q(cardID__cardID=cardID)
            ).exists()

            if paymentDone:
                response["status"] = True
                status = 200
            else:
                response["error"] = "Payment is missing for this card!"
                status = 403

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            response["error"] = DEFAULT_ERROR

        return JsonResponse(data=response, safe=False, status=status)

    elif is_auth_post_student(req):  # Change payment status
        try:
            order_id = req.POST.get("order_id")
            payment_id = req.POST.get("payment_id")
            cardID = req.POST.get("cardID")

            if not (order_id and payment_id):
                response["error"] = "Payment was unsuccessful"
                status = 402

            elif not (cardID):
                response["error"] = "CardID was missing"
                status = 404
    
            else:
                if Card.objects.filter(cardID=cardID).exists(): # Useless as this is after payment
                    paymentDone = razorPayment.objects.filter(
                        user=req.user, cardID__cardID=cardID
                    ).exists()

                    if paymentDone:
                        response["error"] = "Payment is Already Done"
                        response["status"] = True
                        status = 409
                    else:
                        payment = razorPayment(
                            order_id=order_id,
                            payment_id=payment_id,
                            user=req.user,
                            cardID=cardID,
                        )
                        payment.save()

                        response["status"] = True
                        status = 200
                else:
                    response["error"] = "CardID was not found"
                    status = 404

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            response["error"] = DEFAULT_ERROR

        return JsonResponse(data=response, safe=False, status=status)


@csrf_exempt
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
def available_card(req: HttpRequest):
    if is_auth_get_student(req):
        cards: list[CardData] = []
        response = CardResponse(status=False, error=None, cards=cards, nextPage=0, **getRequestToken(req))


        try:
            page = int(req.GET.get("page", "0"))
        except:
            page = 0

        status = 500
        try:
            available_card = (
                razorPayment.objects.filter(Q(user=req.user))
                .order_by("timestamp")
                .defer("cardID", "timestamp")[page : page + MAX_RECORD]
            )

            for card in available_card.iterator():
                cards.append(
                    CardData(
                        cardID=card.cardID.cardID,
                        timestamp=card.timestamp.isoformat(),
                        branch=card.cardID.belongs.name,
                        institute=card.cardID.belongs.institute.name,
                        university=card.cardID.belongs.institute.university.name,
                    )
                )
            response["cards"] = cards
            response["nextPage"] = page + MAX_RECORD
            response["status"] = True
            status = 200

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            response["error"] = DEFAULT_ERROR

        return JsonResponse(data=response, safe=False, status=status)


@csrf_exempt
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
def user_info(req: HttpRequest):
    if is_auth_get_student(req):
        user = get_user(req)

        response = UserInfoResponse(
            status=False,
            error=None,
            email=None,
            username=None,
            **getRequestToken(req),
        )
        
        status = 500

        try:
            response["username"] = user.username
            response["email"] = user.email
            response["status"] = True
            status = 200
        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            response["error"] = DEFAULT_ERROR

        return JsonResponse(data=response, safe=False, status=status)

@csrf_exempt
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
@check_otp_response
def username_form(req: HttpRequest):
    if is_auth_get_student(req):
        f = UsernameChange(req.POST)
        
        if f.is_valid():
            try:
                username = str(f.cleaned_data.get("Username"))

                
                if User.objects.filter(username=username).exists():
                    raise UserNameAlreadyExists(username)

                otpOk: bool = req.__getattribute__("ok")

                if not otpOk:
                    raise OTPWrong()

                user = get_user(req)

                user.username = username
                user.save()

                send_success_mail(req, "username")

            except OTPWrong as e:
                setSwalAlert(context, e.get_error())

            except UserNameAlreadyExists as g:
                setSwalAlert(context, g.get_error())

            except Exception as e:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.EXCEPTION)
                    .set_meta(req)
                    .set_error(e)
                )
                setSwalAlert(context, DEFAULT_ERROR)

        else:
            setSwalAlert(context, f.getErrors())

        return render(req, "Change/HTMX/messages.html", context=context)


@htmx_response
@auth_needed()
@check_otp_response
def htmx_email_form(req: HttpRequest):
    if is_hx_post(req):
        context = setSwalAlert(title="Email Change")
        f = EmailChange(req.POST)

        if f.is_valid():
            try:
                email = str(f.cleaned_data.get("Email"))

                if User.objects.filter(email=email).exists():
                    raise EmailAlreadyExists(email)

                otpOk: bool = req.__getattribute__("ok")
                if not otpOk:
                    raise OTPWrong()

                user = get_user(req)

                user.email = email
                user.save()
                setSwalAlert(context, "Email was changed successfully", "success")
                send_success_mail(req, "email")

                context["redirect"] = req.build_absolute_uri(reverse("User:index"))
                logout(req)

            except OTPWrong as e:
                setSwalAlert(context, e.get_error())

            except EmailAlreadyExists as g:
                setSwalAlert(context, g.get_error())

            except Exception as e:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.EXCEPTION)
                    .set_meta(req)
                    .set_error(e)
                )
                setSwalAlert(context, DEFAULT_ERROR)

        else:
            setSwalAlert(context, f.getErrors())

        return render(req, "Change/HTMX/messages.html", context=context)


@htmx_response
@get_user_from_session
@auth_needed()
@check_otp_response
def htmx_password_form(req: HttpRequest):
    if is_hx_post(req):
        context = setSwalAlert(title="Password Change")
        f = PasswordChange(req.POST)

        if f.is_valid():
            try:
                password = f.cleaned_data.get("Password")

                otpOk: bool = req.__getattribute__("ok")
                if not otpOk:
                    raise OTPWrong()

                user = get_user(req)

                user.set_password(password)
                user.save()
                setSwalAlert(context, "Password was changed successfully", "success")
                send_success_mail(req, "password")

                context["redirect"] = req.build_absolute_uri(reverse("User:index"))
                logout(req)

            except OTPWrong as e:
                setSwalAlert(context, e.get_error())

            except Exception as e:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.EXCEPTION)
                    .set_meta(req)
                    .set_error(e)
                )
                setSwalAlert(context, DEFAULT_ERROR)

        else:
            setSwalAlert(context, f.getErrors())

        return render(req, "Change/HTMX/messages.html", context=context)


@htmx_response
@get_user_from_session
@auth_needed()
@check_otp_response
def send_otp_mail(req: HttpRequest, type: Literal["username", "email", "password"]):
    if is_hx_post(req):
        context = setSwalAlert(title="OTP Mail")
        otp = req.__getattribute__("otp")
        user = get_user(req)

        send_ok = False

        if otp:
            send_ok = email_send(
                OTP_SUBJECT.format(type.capitalize()),
                user.email,
                OTP_MESSAGE.format(type.capitalize(), otp),
            )

        if send_ok:
            setSwalAlert(context, "OTP has been send to your email", "success")
        else:
            setSwalAlert(context, "Failed to send email. Please try again!")

        return render(req, "Change/HTMX/messages.html", context=context)


def forgot_password(req: HttpRequest):
    if req.method == "GET":
        return render(
            req, "Change/HTML/forgot.password.html", context={"form": ForgotEmail()}
        )


@htmx_response
@read_body_as_form
@check_otp_response
def send_otp_mail_password(req: SpecialHttpRequest):
    if is_hx_post(req):
        context = setSwalAlert(title="OTP Mail")
        otp = req.__getattribute__("otp")
        user = get_user(req)

        send_ok = False

        if otp:
            send_ok = email_send(
                OTP_SUBJECT.format("Password"),
                user.email,
                OTP_MESSAGE.format("Password", otp),
            )

        if send_ok:
            setSwalAlert(context, "OTP has been send to your email", "success")
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
                context["redirect"] = req.build_absolute_uri(
                    reverse("Change:passChange")
                )

                setSwalAlert(text="Email was found!", icon="success")

            except User.DoesNotExist:
                setSwalAlert(context, text="Email is not registered")

            except Exception as e:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.EXCEPTION)
                    .set_meta(req)
                    .set_error(e)
                )
                setSwalAlert(context, DEFAULT_ERROR)

        else:
            setSwalAlert(context, text=f.getErrors())

        return render(req, "Change/HTMX/messages.html", context=context)


@htmx_response
@auth_needed()
@check_otp_response
def htmx_delete_form(req: HttpRequest):
    if is_hx_post(req):
        context = setSwalAlert(title="Username Change")
        f = DeleteAccount(req.POST)

        if f.is_valid():
            try:
                otpOk: bool = req.__getattribute__("ok")

                if not otpOk:
                    raise OTPWrong()

                user = get_user(req)

                user.delete()

                setSwalAlert(context, "Account was successfully deleted", "success")
                send_success_mail(req, "username")
                logout(req)

            except OTPWrong as e:
                setSwalAlert(context, e.get_error())

            except Exception as e:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.EXCEPTION)
                    .set_meta(req)
                    .set_error(e)
                )
                setSwalAlert(context, DEFAULT_ERROR)

        else:
            setSwalAlert(context, f.getErrors())

        return render(req, "Change/HTMX/messages.html", context=context):wait

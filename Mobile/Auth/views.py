from django.http import HttpRequest, JsonResponse  # type: ignore
from Logs.loggers import APP_LOG, LogStructure, LogType
from Register.errors import UserExists
from University.models import Branch
from constants import DEFAULT_ERROR
from tools.url_auth import (
    AccessPayLoad,
    RefreshPayLoad,
    read_body_as_json,
    is_auth_get_student,
    get_user,
    getRequestToken,
    jwt_required,
    student_auth_needed,
)
from django.db.models import Q  # type: ignore
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from django.db import transaction  # type: ignore
from User.models import User, Role, RoleType, is_student
from Mobile.types import LoginResponse, RegisterResponse, UserInfoResponse
from Mobile.Auth.forms import RegisterForm, LoginForm


@csrf_exempt
@read_body_as_json
def mobile_login(req: HttpRequest):
    if req.method == "POST":
        response = LoginResponse(status=False, error=[], access=None, refresh=None)
        status: int = 500

        f = LoginForm(req.POST)

        try:
            if f.is_valid():
                username = f.cleaned_data.get("user")
                password = f.cleaned_data.get("password")

                user = User.objects.get(username=username)

                if is_student(user) and user.check_password(password):
                    response["access"] = AccessPayLoad(user).getToken()
                    response["refresh"] = RefreshPayLoad(user).getToken()
                    response["status"] = True
                    status = 200

                else:
                    response["error"] = ["Incorrect Credentials"]
                    status = 403

            else:
                response["error"] = f.getJsonErrors()

        except User.DoesNotExist:
            status = 401
            response["error"] = ["Invalid credentials"]

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            response["error"] = [DEFAULT_ERROR]

        return JsonResponse(data=response, safe=False, status=status)


@csrf_exempt
@read_body_as_json
def mobile_register(req: HttpRequest):
    if req.method == "POST":
        response = RegisterResponse(access=None, refresh=None, status=False, error=[])
        status = 500
        f = RegisterForm(req.POST)

        try:
            with transaction.atomic():
                if f.is_valid():
                    user = str(f.cleaned_data.get("username", ""))
                    email = str(f.cleaned_data.get("email", ""))
                    password = str(f.cleaned_data.get("password", ""))
                    branch = str(f.cleaned_data.get("branch", ""))

                    exists = User.objects.filter(
                        Q(username=user) | Q(email=email)
                    ).exists()

                    if not branch.isnumeric():
                        raise Branch.DoesNotExist()

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
                    response["error"] = f.getJsonErrors()
                    status = 400
        except UserExists as f:
            status = 403
            response["error"] = ["Username or Email is already registered!"]

        except Branch.DoesNotExist:
            status = 401
            response["error"] = ["Branch was not found!"]

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            status = 500
            response["error"] = [DEFAULT_ERROR]

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
            error=[],
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
            response["error"] = [DEFAULT_ERROR]

        return JsonResponse(data=response, safe=False, status=status)

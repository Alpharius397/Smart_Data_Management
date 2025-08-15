from django.http import HttpRequest, JsonResponse  # type: ignore
from Logs.loggers import APP_LOG, LogStructure, LogType
from User.models import get_user
from constants import DEFAULT_ERROR, MAX_RECORD
from Mobile.models import razorPayment
from Mobile.url_auth import (
    getRequestToken,
    is_auth_get_student,
    is_auth_post_student,
    jwt_required,
    read_body_as_json,
    student_auth_needed,
)
from django.views.decorators.http import require_http_methods
from django.db.models import Q  # type: ignore
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from Card.models import Card
from Mobile.types import SubscriberResponse, CardResponse, CardData


@csrf_exempt
@require_http_methods(["GET", "POST"])
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
def getReport(req: HttpRequest):
    pass

from hashlib import sha256
import hmac
from django.http import HttpRequest, JsonResponse  # type: ignore
from Logs.loggers import APP_LOG, LogStructure, LogType
from Mobile.Cards.forms import HeadingForm
from University.models import Branch, Institute, University
from User.models import get_user
from constants import DEFAULT_ERROR, MAX_RECORD
from Mobile.models import razorPayment
from Mobile.url_auth import (
    is_auth_get_student,
    is_auth_post_student,
    jwt_required,
    read_body_as_json,
    student_auth_needed,
)
from django.db.models import Q  # type: ignore
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from Card.models import Card
from Mobile.types import HeadingResponse, SubscriberResponse, CardResponse, CardData
from tools.encrypt import encryptionRSA, verify_signature
from tools.url_auth import require_http_methods
from tools.utils import tryCatchThis
from Main.settings import settingsInterface as settings


@csrf_exempt
@require_http_methods(["GET", "POST"])
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
def subscriber_check(req: HttpRequest):
    response = SubscriberResponse(
        status=False, error=[], key=None, decryptionKey=None
    )
    user = get_user(req)
    status = 500

    if is_auth_get_student(req):  # Check if user has paid money
        try:
            cardID = str(req.GET.get("cardID"))
            pubKey = str(req.GET.get("pubKey"))

            paymentDone = razorPayment.objects.filter(
                user__id=user.id, cardID__cardID__exact=cardID
            )

            if (paymentDone.exists() and ((payment := paymentDone.first()) is not None)):
                response["decryptionKey"] = encryptionRSA(settings.DECRYPTION_KEY, pubKey)
                response["status"] = True
                response["key"] = payment.cardID.decryption_key
            
                status = 200
            else:
                response["error"] = ["Payment is missing for this card!"]
                status = 403

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            response["error"] = [DEFAULT_ERROR]

        return JsonResponse(data=response, safe=False, status=status)

    elif is_auth_post_student(req):  # Change payment status
        try:
            order_id = req.POST.get("order_id")
            payment_id = req.POST.get("payment_id")
            cardID = req.POST.get("cardID")
            razorpay_signature = req.POST.get("razorpay_signature")

            if not (order_id and payment_id and razorpay_signature):
                response["error"] = ["Payment was unsuccessful"]
                status = 402

            elif not (cardID):
                response["error"] = ["CardID was missing"]
                status = 404

            else:
                if Card.objects.filter(
                    cardID=cardID
                ).exists():  # Useless as this is after payment
                    paymentDone = razorPayment.objects.filter(
                        user=user, cardID__cardID=cardID
                    ).exists()

                    if paymentDone:
                        response["error"] = ["Payment is Already Done"]
                        response["status"] = True
                        status = 409
                    else:
                        if verify_signature(order_id, payment_id, razorpay_signature):
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
                            status = 403
                            response["error"] = ["Invalid Signature of Payment"]
                else:
                    response["error"] = ["CardID was not found"]
                    status = 404

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
@require_http_methods(["GET"])
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
def available_card(req: HttpRequest):
    if is_auth_get_student(req):
        cards: list[CardData] = []
        response = CardResponse(
            status=False, error=[], cards=cards, nextPage=0
        )

        user = get_user(req)

        try:
            page = int(req.GET.get("page", "0"))
        except ValueError:
            page = 0

        status = 500
        try:
            available_card = (
                razorPayment.objects.filter(Q(user=user))
                .order_by("timestamp")
                .reverse()
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
            response["error"] = [DEFAULT_ERROR]

        return JsonResponse(data=response, safe=False, status=status)


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
def get_heading(req: HttpRequest):
    if is_auth_get_student(req):
        f = HeadingForm(req.GET)

        response = HeadingResponse(
            status=False,
            error=[],
            university=None,
            institute=None,
            branch=None,
        )
        
        status = 400
        if f.is_valid():
            uniID = str(f.cleaned_data.get("university", ""))
            instiID = str(f.cleaned_data.get("institute", ""))
            branchID = str(f.cleaned_data.get("branch", ""))

            """ Hacky  but okay """
            university = tryCatchThis(University.objects.get, None)(id=uniID)
            institute = tryCatchThis(Institute.objects.get, None)(id=instiID)
            branch = tryCatchThis(Branch.objects.get, None)(id=branchID)

            response["university"] = None if (university is None) else university.name
            response["institute"] = None if (institute is None) else institute.name
            response["branch"] = None if (branch is None) else branch.name
            response["status"] = True
            status = 200
        else:
            response["error"] = f.getJsonErrors()

        return JsonResponse(data=response, safe=False, status=status)

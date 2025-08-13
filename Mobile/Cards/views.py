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
from django.db.models import Q  # type: ignore
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from Card.models import Card
from Mobile.types import SubscriberResponse, CardResponse, CardData


@csrf_exempt
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
def subscriber_check(req: HttpRequest):
    response = SubscriberResponse(status=False, error=[], **getRequestToken(req))
    user = get_user(req)
    status = 500

    if is_auth_get_student(req):  # Check if user has paid money
        try:
            cardID = str(req.GET.get("cardID"))

            paymentDone = razorPayment.objects.filter(
                user__id=user.id, cardID__cardID__exact=cardID
            )

            if paymentDone:
                response["status"] = True
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

            if not (order_id and payment_id):
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
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
def available_card(req: HttpRequest):
    if is_auth_get_student(req):
        cards: list[CardData] = []
        response = CardResponse(
            status=False, error=[], cards=cards, nextPage=0, **getRequestToken(req)
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

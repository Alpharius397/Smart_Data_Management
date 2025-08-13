from django.core.mail import send_mail  # type: ignore
from django.core.validators import validate_email  # type: ignore
from Logs.loggers import SMTP_LOG
from typing import Literal
from django.http import HttpRequest  # type: ignore
from User.models import get_user
from constants import SUCCESS_MESSAGE, SUCCESS_SUBJECT, DELETE_MESSAGE, DELETE_SUBJECT
from celery import shared_task
from Main import celery_app


""" In Prod: shared_task, else celery_app.task """


@celery_app.task()
def email_send(subject: str, to_email: str, message: str):
    try:
        validate_email(to_email)  # Validate Email
        send_mail(
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=[to_email],
            fail_silently=False,
        )
    except Exception as e:
        SMTP_LOG.write_error(SMTP_LOG.get_error_info(e))


def send_success_mail(req: HttpRequest, type: Literal["username", "email", "password"]):
    user = get_user(req)
    email_send.delay(
        SUCCESS_SUBJECT.format(type.capitalize()),
        user.email,
        SUCCESS_MESSAGE.format(type.capitalize()),
    )


def send_delete_mail(req: HttpRequest):
    user = get_user(req)
    email_send.delay(DELETE_SUBJECT, user.email, DELETE_MESSAGE.format(user.username))

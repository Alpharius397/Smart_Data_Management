from django.core.mail import send_mail # type: ignore
from django.core.validators import validate_email # type: ignore

def email_send(subject: str, to_email: str, message: str) -> bool:
    try:
        validate_email(to_email) # Validate Email
        ok_send = send_mail(subject=subject, message=message, from_email=None, recipient_list=[to_email], fail_silently=False)
        return (ok_send == 1)
    except Exception as e:
        return False

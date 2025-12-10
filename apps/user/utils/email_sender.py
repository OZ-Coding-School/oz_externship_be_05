from django.core.mail import send_mail
from django.conf import settings

def send_verification_email(to_email: str, code: str, purpose: str) -> None:
    subject = f"[{purpose}] 이메일 인증 코드"
    message = f"인증코드: {code}\n5분 안에 입력하시오."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email])
    
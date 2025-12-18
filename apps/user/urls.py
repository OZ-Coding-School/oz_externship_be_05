from django.urls import path

from apps.user.views import social_login_views
from apps.user.views.auth import (
    LoginAPIView,
    SignupAPIView,
)
from apps.user.views.verification import (
    SendEmailAPIView,
    SendSMSVerificationAPIView,
    VerifyEmailAPIView,
    VerifySMSAPIView,
)

urlpatterns = [
    path("social-login/kakao", social_login_views.KakaoLoginStartAPIView.as_view(), name="kakao-login-start"),
    path("social-login/kakao/callback", social_login_views.KakaoCallbackAPIView.as_view(), name="kakao-callback"),
    path("social-login/naver", social_login_views.NaverLoginStartAPIView.as_view(), name="naver-login-start"),
    path("social-login/naver/callback", social_login_views.NaverCallbackAPIView.as_view(), name="naver-callback"),
    path("signup", SignupAPIView.as_view(), name="signup"),
    path("login", LoginAPIView.as_view(), name="login"),
    path("verification/send-sms", SendSMSVerificationAPIView.as_view(), name="send_sms"),
    path("verification/verify-sms", VerifySMSAPIView.as_view(), name="verify_sms"),
    path("verification/send-email", SendEmailAPIView.as_view(), name="signup_send_email"),
    path("verification/verify-email", VerifyEmailAPIView.as_view(), name="signup_verify_email"),
]

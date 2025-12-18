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

# from django.urls import path

# urlpatterns = [
#     # 수강생 CRUD
#     path(
#         "admin/accounts",
#     ),
#     path(
#         "admin/accounts/<int:account_id>",
#     ),
#     path(
#         "admin/accounts/<int:account_id>/role",
#     ),
#     path(
#         "admin/accounts/students",
#     ),
#     # 수강생 등록
#     path(
#         "admin/accounts/students-enrollments",
#     ),
#     path(
#         "admin/accounts/students-enrollments/accept",
#     ),
#     path(
#         "admin/accounts/students-enrollments/reject",
#     ),
#     # 회원 탈퇴
#     path(
#         "admin/accounts/withdrawals",
#     ),
#     path(
#         "admin/accounts/withdrawals/<int:withdrawal_id>",
#     ),
#     # 분석 API
#     path(
#         "admin/accounts/analytics/signup/trends",
#     ),
#     path(
#         "admin/analytics/withdrawals/trends",
#     ),
#     path(
#         "admin/analytics/withdrawal-reasons/percentage",
#     ),
#     path(
#         "admin/analytics/withdrawal-reasons/stats/monthly",
#     ),
#     path(
#         "admin/analytics/student-enrollments/trends",
#     ),
#     path(
#         "admin/accounts",
#     ),
#     path(
#         "admin/accounts",
#     ),
#     path(
#         "admin/accounts",
#     ),
# ]

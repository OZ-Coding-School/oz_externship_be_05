from django.urls import path

from apps.user.views import social_login_views
from apps.user.views.account import (
    ChangePasswordAPIView,
    ChangePhoneAPIView,
    CheckNicknameAPIView,
    MeAPIView,
    ProfileImageAPIView,
)
from apps.user.views.auth import (
    LoginAPIView,
    RefreshAPIView,
    SignupAPIView,
)
from apps.user.views.enrollemnt import EnrolledCoursesAPIView, EnrollStudentAPIView
from apps.user.views.recovery import (
    FindEmailAPIView,
    FindPasswordAPIView,
    RestoreAccountAPIView,
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
    path("refresh", RefreshAPIView.as_view(), name="refresh"),
    path("me", MeAPIView.as_view(), name="me"),
    path("me/profile-image", ProfileImageAPIView.as_view(), name="me_profile_image"),
    path("me/enrolled-courses", EnrolledCoursesAPIView.as_view(), name="me_enrolled_courses"),
    path("enroll-student", EnrollStudentAPIView.as_view(), name="enroll_student"),
    path("change-password", ChangePasswordAPIView.as_view(), name="change_password"),
    path("change-phone", ChangePhoneAPIView.as_view(), name="change_phone"),
    path("check-nickname", CheckNicknameAPIView.as_view(), name="check_nickname"),
    path("verification/send-sms", SendSMSVerificationAPIView.as_view(), name="send_sms"),
    path("verification/verify-sms", VerifySMSAPIView.as_view(), name="verify_sms"),
    path("verification/send-email", SendEmailAPIView.as_view(), name="signup_send_email"),
    path("verification/verify-email", VerifyEmailAPIView.as_view(), name="signup_verify_email"),
    path("restore", RestoreAccountAPIView.as_view(), name="restore_account"),
    path("find-email", FindEmailAPIView.as_view(), name="find_email"),
    path("find-password", FindPasswordAPIView.as_view(), name="find_password"),
]

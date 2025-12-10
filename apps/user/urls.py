from django.urls import path
from apps.user.views import email_views, sms_views, social_login_views

urlpatterns = [
    # 로그인
    # path("signup/"),
    # path("me/presigned-url/",),

    # 이메일
    path("signup/send-email/",email_views.SignupSendEmailAPIView.as_view(),name="회원가입 이메일 전송 API"),
    path("signup/verify-email/",email_views.SignupVerifyEmailAPIView.as_view(),name="회원가입 이메일 인증 API"),
    # path("accounts/login/",),

    # sms
    path("verification/send-sms/",sms_views.SendSmsCode.as_view(),name="SMS 인증번호 전송 API"),
    path("verification/verify-sms/",sms_views.VerifySMSCodeToken.as_view(),name="SMS 인증번호 검증 API"),
    path("verification/find-email",sms_views.FindEmailViaSMS.as_view(),name="SMS로 이메일 찾기 API"),

    # 소셜 로그인
    path("social-login/kakao/",social_login_views.KakaoLoginStartAPIView.as_view(),name="카카오 Oauth 토큰 발급 API"),
    path("social-login/naver/",social_login_views.NaverLoginStartAPIView.as_view(),name="네이버 Oauth 토큰 발급 API"),
    path("social-login/kakao/callback",social_login_views.KakaoCallbackAPIView.as_view(),name="카카오 Oauth CallBack API"),
    path("social-login/naver/callback",social_login_views.NaverCallbackAPIView.as_view(),name="네이버 Oauth CallBack API"),

    # # 비번찾기
    # path("change-password/",),
    path("find-password/",email_views.FindPasswordAPIView.as_view(),name="비밀번호 찾기 API"),
    path("find-password/send-email/",email_views.SignupSendEmailAPIView,name="비밀번호 찾기 이메일 전송 API"),
    # path("find-password/verify-email/",),

    # # 계정복구
    path("restore/",email_views.RestoreAPIView.as_view(),name="이메일로 계정 찾기 API"),
    path("restore/send-email/",email_views.RestoreSendEmailAPIView.as_view(),name="이메일로 계정 찾기 메일 전송 API"),

    # # 닉네임 중복 확인
    # path("check-nickname/",),

    # # 휴대폰 번호 변경
    # path("change-phone/",),

    # # 수강생 등록 신청
    # path("enroll-student/",),
    # # 내 정보 조회
    # path("me/",),

    # # 수강 목록 조회
    # path("me/enrolled-courses/",),
]
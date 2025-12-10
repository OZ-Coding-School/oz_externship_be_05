from django.urls import path

urlpatterns = [
    # 로그인
    path("signup/",),
    path("me/presigned-url/",),
    path("signup/send-email",),
    path("signup/verify-email/",),

    # sms
    path("verify/sendsms/",),
    path("verify/sms/",),
    path("api/v1/accounts/login/",),

    # 소셜 로그인
    path("social-login/kakao/",),
    path("social-login/naver/",),
    path("social-login/kakao/callback/",),
    path("social-login/naver/callback/",),

    # 비번찾기
    path("change-password/",),
    path("find-password/",),
    path("find-password/send-email/",),
    path("find-password/verify-email/",),
    path("find-email/",),

    # 계정복구
    path("restore/",),
    path("restore/send-email/",),

    # 닉네임 중복 확인
    path("check-nickname/",),

    # 휴대폰 번호 변경
    path("change-phone/",),

    # 수강생 등록 신청
    path("enroll-student/",),
    # 내 정보 조회
    path("me/",),

    # 수강 목록 조회
    path("me/enrolled-courses/",),
]
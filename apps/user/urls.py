from django.urls import path

from apps.user.views import social_login_views

urlpatterns = [
    path("kakao/", social_login_views.KakaoLoginStartAPIView.as_view(), name="kakao-login-start"),
    path("kakao/callback/", social_login_views.KakaoCallbackAPIView.as_view(), name="kakao-callback"),

    path("naver/", social_login_views.NaverLoginStartAPIView.as_view(), name="naver-login-start"),
    path("naver/callback/", social_login_views.NaverCallbackAPIView.as_view(), name="naver-callback"),
]

from django.urls import path
from apps.user.views import social_login_views

urlpatterns = [
    path("social-login/kakao/",social_login_views.KakaoLoginStartAPIView.as_view(),name="카카오 Oauth 토큰 발급 API"),
    path("social-login/naver/",social_login_views.NaverLoginStartAPIView.as_view(),name="네이버 Oauth 토큰 발급 API"),
    path("social-login/kakao/callback",social_login_views.KakaoCallbackAPIView.as_view(),name="카카오 Oauth CallBack API"),
    path("social-login/naver/callback",social_login_views.NaverCallbackAPIView.as_view(),name="네이버 Oauth CallBack API"),
]
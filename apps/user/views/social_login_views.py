from django.shortcuts import redirect
from django.http import HttpResponseBadRequest
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.user.utils.social_login import (
    KakaoOAuthService,
    NaverOAuthService,
    get_or_create_kakao_user,
    get_or_create_naver_user,
)


class KakaoLoginStartAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):
        SCOPES = [
            "profile_nickname",
            "profile_image",
            "account_email",
            "gender",
            "birthday",
            "age_range",
        ]

        scope_str = ",".join(SCOPES)

        authorize_url = (
            f"{KakaoOAuthService.AUTHORIZE_URL}"
            f"?response_type=code"
            f"&client_id={settings.KAKAO_CLIENT_ID}"
            f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
            f"&scope={scope_str}"
        )
        return redirect(authorize_url)


class NaverLoginStartAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):
        import uuid
        state = uuid.uuid4().hex

        authorize_url = (
            f"https://nid.naver.com/oauth2.0/authorize"
            f"?response_type=code"
            f"&client_id={settings.NAVER_CLIENT_ID}"
            f"&redirect_uri={settings.NAVER_REDIRECT_URI}"
            f"&state={state}"
        )
        return redirect(authorize_url) 


class KakaoCallbackAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get("code")
        if not code:
            return HttpResponseBadRequest("code is required")

        service = KakaoOAuthService()
        access_token = service.get_access_token(code)
        profile = service.get_user_info(access_token)

        user = get_or_create_kakao_user(profile)

        refresh = RefreshToken.for_user(user)

        redirect_url = (
            f"{settings.FRONTEND_SOCIAL_SUCCESS_URL}"
            f"?access={refresh.access_token}&refresh={refresh}"
        )

        return redirect(redirect_url)


class NaverCallbackAPIView(APIView):
    
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code or not state:
            return HttpResponseBadRequest("code and state are required")

        service = NaverOAuthService()
        access_token = service.get_access_token(code, state)
        profile = service.get_user_info(access_token)

        user = get_or_create_naver_user(profile)

        refresh = RefreshToken.for_user(user)

        redirect_url = (
            f"{settings.FRONTEND_SOCIAL_SUCCESS_URL}"
            f"?access={refresh.access_token}&refresh={refresh}"
        )

        return redirect(redirect_url)
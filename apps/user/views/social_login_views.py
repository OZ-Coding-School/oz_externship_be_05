from typing import Any, Literal, cast
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.user.serializers.social_profile import (
    KakaoProfileSerializer,
    NaverProfileSerializer,
)
from apps.user.utils.social_login import (
    KakaoOAuthService,
    NaverOAuthService,
)


def frontend_redirect(*, provider: str, error: str | None = None) -> HttpResponseRedirect:
    base = getattr(settings, "FRONTEND_SOCIAL_REDIRECT_URL", "")
    params = {"provider": provider}
    if error:
        params["error"] = error
    return redirect(f"{base}?{urlencode(params)}")


def auth_cookies(resp: HttpResponseRedirect, *, access: str, refresh: str) -> None:
    secure = getattr(settings, "SESSION_COOKIE_SECURE", False)
    samesite = cast(Literal["Lax", "Strict", "None", False] | None, getattr(settings, "SESSION_COOKIE_SAMESITE", "Lax"))

    resp.set_cookie(
        "access",
        access,
        httponly=False,
        secure=secure,
        samesite=samesite,
        path="/",
    )

    resp.set_cookie(
        "refresh",
        refresh,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )


class KakaoLoginStartAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> HttpResponseRedirect:
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

    def get(self, request: Request) -> HttpResponseRedirect:
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

    def get(self, request: Request) -> HttpResponseRedirect:
        code = request.query_params.get("code")
        if not code:
            return frontend_redirect(provider="kakao", error="code_required")

        service = KakaoOAuthService()
        access_token = service.get_access_token(code)
        profile = service.get_user_info(access_token)

        serializer = KakaoProfileSerializer(data=profile)
        serializer.is_valid(raise_exception=True)

        user = service.get_or_create_user(profile)

        if not user.is_active:
            return frontend_redirect(provider="kakao", error="inactive")

        refresh = RefreshToken.for_user(user)

        resp = frontend_redirect(provider="kakao")
        auth_cookies(resp, access=str(refresh.access_token), refresh=str(refresh))
        return resp


class NaverCallbackAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> HttpResponseRedirect:
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code or not state:
            return frontend_redirect(provider="naver", error="code_state_required")

        service = NaverOAuthService()
        access_token = service.get_access_token(code, state)
        profile = service.get_user_info(access_token)

        serializer = NaverProfileSerializer(data=profile)
        serializer.is_valid(raise_exception=True)

        user = service.get_or_create_user(serializer.validated_data)

        if not user.is_active:
            return frontend_redirect(provider="naver", error="inactive")

        refresh = RefreshToken.for_user(user)

        resp = frontend_redirect(provider="naver")
        auth_cookies(resp, access=str(refresh.access_token), refresh=str(refresh))
        return resp

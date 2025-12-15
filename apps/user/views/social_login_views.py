import logging
import uuid
from typing import Any, Literal, cast
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
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

logger = logging.getLogger(__name__)


def frontend_redirect(*, provider: str, is_success: bool = True) -> HttpResponseRedirect:
    base = getattr(settings, "FRONTEND_SOCIAL_REDIRECT_URL", "") or "/"
    params = {"provider": provider, "is_success": is_success}
    return redirect(f"{base}?{urlencode(params)}")


def auth_cookies(resp: HttpResponseRedirect, *, access: str, refresh: str) -> None:
    secure = getattr(settings, "SESSION_COOKIE_SECURE", False)  #! https에서만 가능할지 환경변수로 관리할지 물어볼 것
    samesite = cast(
        Literal["Lax", "Strict", "None", False] | None, getattr(settings, "SESSION_COOKIE_SAMESITE", "Lax")
    )  #! 쿠키를 어디까지 허용할지 이것도 환경변수

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

    @extend_schema(
        tags=["Social Login"],
        summary="카카오 로그인 시작",
        responses={302: None},
    )
    def get(self, request: Request) -> HttpResponseRedirect:
        state = uuid.uuid4().hex
        request.session["oauth_state_kakao"] = state

        authorize_url = (
            f"{KakaoOAuthService.AUTHORIZE_URL}"
            f"?response_type=code"
            f"&client_id={settings.KAKAO_CLIENT_ID}"
            f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
            f"&state={state}"
        )
        return redirect(authorize_url)


class NaverLoginStartAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Social Login"],
        summary="네이버 로그인 시작",
        responses={302: None},
    )
    def get(self, request: Request) -> HttpResponseRedirect:
        state = uuid.uuid4().hex
        request.session["oauth_state_naver"] = state

        authorize_url = (
            f"{NaverOAuthService.AUTHORIZE_URL}"
            f"?response_type=code"
            f"&client_id={settings.NAVER_CLIENT_ID}"
            f"&redirect_uri={settings.NAVER_REDIRECT_URI}"
            f"&state={state}"
        )
        return redirect(authorize_url)


class KakaoCallbackAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Social Login"],
        summary="카카오 로그인 콜백",
        parameters=[],
        responses={302: None, 400: None, 403: None},
    )

    #! status 스키마 추가.
    def get(self, request: Request) -> HttpResponseRedirect:
        try:
            code = request.query_params.get("code")
            state = request.query_params.get("state")
            # code, state 유무 검증.
            if not code or not state:
                raise ValidationError({"code": "code_state_required"})

            # state를 확인하여 올바른 곳에서 온 요청인지 검증.
            if state != request.session.get("oauth_state_kakao"):
                raise ValidationError({"code": "invalid state"})

            service = KakaoOAuthService()
            access_token = service.get_access_token(code)
            profile = service.get_user_info(access_token)

            serializer = KakaoProfileSerializer(data=profile)
            serializer.is_valid(raise_exception=True)

            user = service.get_or_create_user(profile)

            # 비활성화 유저인지 검증
            if not user.is_active:
                raise ValidationError({"code": "inactive_user"})

            refresh = RefreshToken.for_user(user)

            resp = frontend_redirect(provider="kakao")
            auth_cookies(resp, access=str(refresh.access_token), refresh=str(refresh))
            return resp

        except ValidationError as e:
            logger.warning("kakao callback validation error: %s", e.detail)
            return frontend_redirect(provider="kakao", is_success=False)
        except requests.exceptions.HTTPError:
            logger.exception("kakao callback oauth http error")
            return frontend_redirect(provider="kakao", is_success=False)
        except Exception:
            logger.exception("kakao callback unexpected error")
            return frontend_redirect(provider="kakao", is_success=False)
        finally:
            request.session.pop("oauth_state_kakao", None)


class NaverCallbackAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Social Login"],
        summary="네이버 로그인 콜백",
        parameters=[],
        responses={302: None, 400: None, 403: None},
    )
    def get(self, request: Request) -> HttpResponseRedirect:
        try:
            code = request.query_params.get("code")
            state = request.query_params.get("state")
            # code, state 유무 검증.
            if not code or not state:
                raise ValidationError({"code": "code_state_required"})

            # state를 확인하여 올바른 곳에서 온 요청인지 검증.
            if state != request.session.get("oauth_state_naver"):
                raise ValidationError({"code": "invalid_status"})

            service = NaverOAuthService()
            access_token = service.get_access_token(code, state)
            profile = service.get_user_info(access_token)

            serializer = NaverProfileSerializer(data=profile)
            serializer.is_valid(raise_exception=True)

            user = service.get_or_create_user(serializer.validated_data)

            # 비활성화 유저인지 검증.
            if not user.is_active:
                raise ValidationError({"code": "inactive_user"})

            refresh = RefreshToken.for_user(user)

            resp = frontend_redirect(provider="naver")
            auth_cookies(resp, access=str(refresh.access_token), refresh=str(refresh))
            return resp

        except ValidationError as e:
            logger.warning("naver callback validation error: %s", e.detail)
            return frontend_redirect(provider="naver", is_success=False)
        except requests.exceptions.HTTPError:
            logger.exception("naver callback oauth http error")
            return frontend_redirect(provider="naver", is_success=False)
        except Exception:
            logger.exception("naver callback unexpected error")
            return frontend_redirect(provider="naver", is_success=False)
        finally:
            request.session.pop("oauth_state_naver", None)

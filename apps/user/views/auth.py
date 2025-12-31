from __future__ import annotations

from typing import Literal, cast

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.user.models import User
from apps.user.serializers.auth import (
    LoginSerializer,
    SignupSerializer,
    TokenRefreshSerializer,
)
from apps.user.utils.tokens import issue_token_pair


class SignupAPIView(APIView):

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["회원관리"],
        summary="회원가입 폼 제출 API",
        request=SignupSerializer,
        responses={201: None},
    )
    def post(self, request: Request) -> Response:
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "회원가입이 완료되었습니다."}, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["회원관리"],
        summary="로그인 폼 제출 API",
        request=LoginSerializer,
        responses={200: None},
    )
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user: User = serializer.validated_data["user"]
        return issue_token_pair(RefreshToken.for_user(user))


class RefreshAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["회원관리"],
        summary="리프레시 토큰으로 액세스 토큰 재발급 API",
        request=TokenRefreshSerializer,
        responses={200: None},
    )
    def post(self, request: Request) -> Response:
        data = dict(request.data)
        if not data.get("refresh_token"):
            cookie_refresh = request.COOKIES.get("refresh_token")
            if cookie_refresh:
                data["refresh_token"] = cookie_refresh
        serializer = TokenRefreshSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return issue_token_pair(RefreshToken(serializer.validated_data["refresh_token"]))


class LogoutAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["회원관리"],
        summary="유저 로그아웃 API",
        responses={200: None},
    )
    def post(self, request: Request) -> Response:
        samesite = cast(
            Literal["Lax", "Strict", "None", False] | None, getattr(settings, "SESSION_COOKIE_SAMESITE", "Lax")
        )
        if settings.DEBUG:
            samesite = "None"
        response = Response({"detail": "로그아웃 되었습니다."}, status=status.HTTP_200_OK)
        response.delete_cookie("refresh_token", path="/", samesite=samesite)
        response.delete_cookie("access_token", path="/", samesite=samesite)
        return response

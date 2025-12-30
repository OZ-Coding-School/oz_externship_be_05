from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import Withdrawal
from apps.user.serializers.recovery import (
    FindEmailSerializer,
    FindPasswordSerializer,
    RestoreAccountSerializer,
)


class RestoreAccountAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["회원관리"],
        summary="이메일 토큰으로 계정 복구 API",
        request=RestoreAccountSerializer,
        responses={200: None},
    )
    def patch(self, request: Request) -> Response:
        serializer = RestoreAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        Withdrawal.objects.filter(user=user).delete()
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active", "updated_at"])
        return Response({"detail": "account restored"}, status=status.HTTP_200_OK)


class FindEmailAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["회원관리"],
        summary="SMS 토큰으로 이메일 찾기 API",
        request=FindEmailSerializer,
        responses={200: None},
    )
    def post(self, request: Request) -> Response:
        serializer = FindEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"masked_email": serializer.validated_data["masked_email"]}, status=status.HTTP_200_OK)


class FindPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["회원관리"],
        summary="이메일 토큰으로 비밀번호 초기화 API",
        request=FindPasswordSerializer,
        responses={200: None},
    )
    def post(self, request: Request) -> Response:
        serializer = FindPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return Response({"detail": "password updated"}, status=status.HTTP_200_OK)

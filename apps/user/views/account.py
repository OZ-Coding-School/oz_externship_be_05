from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import User, Withdrawal, WithdrawalReason
from apps.user.serializers.account import (
    ChangePasswordSerializer,
    ChangePhoneSerializer,
    NicknameCheckSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
)


def get_authenticated_user(request: Request) -> User:
    user = request.user
    if not isinstance(user, User):
        raise NotAuthenticated()
    return user


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = get_authenticated_user(request)
        return Response(UserProfileSerializer(user).data, status=status.HTTP_200_OK)

    def patch(self, request: Request) -> Response:
        user = get_authenticated_user(request)
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserProfileSerializer(user).data, status=status.HTTP_200_OK)

    def delete(self, request: Request) -> Response:
        user = get_authenticated_user(request)
        payload = request.data
        reason_value = payload.get("reason") or WithdrawalReason.OTHER
        if reason_value not in WithdrawalReason.values:
            reason_value = WithdrawalReason.OTHER
        detail = payload.get("reason_detail")
        grace_days = getattr(settings, "WITHDRAWAL_GRACE_DAYS", 14)
        due_date = timezone.now().date() + timedelta(days=grace_days)

        Withdrawal.objects.update_or_create(
            user=user,
            defaults={"reason": reason_value, "reason_detail": detail, "due_date": due_date},
        )
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class CheckNicknameAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = NicknameCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nickname = serializer.validated_data["nickname"]
        if User.objects.filter(nickname__iexact=nickname).exists():
            return Response({"error_detail": "중복된 닉네임이 존재합니다."}, status=status.HTTP_409_CONFLICT)
        return Response({"detail": "사용가능한 닉네임 입니다."}, status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = get_authenticated_user(request)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return Response({"detail": "비밀번호가 변경되었습니다."}, status=status.HTTP_200_OK)


class ChangePhoneAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request) -> Response:
        serializer = ChangePhoneSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = get_authenticated_user(request)
        serializer.update(user, serializer.validated_data)
        return Response({"phone_number": user.phone_number}, status=status.HTTP_200_OK)

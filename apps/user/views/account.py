from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import OpenApiRequest, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.constants import USER_PROFILE_IMAGE_UPLOAD_PATH
from apps.core.utils.image_resizer import ImageResizer
from apps.user.models import User, Withdrawal, WithdrawalReason
from apps.user.serializers.account import (
    ChangePasswordSerializer,
    ChangePhoneSerializer,
    NicknameCheckSerializer,
    ProfileImageUploadSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    WithdrawalRequestSerializer,
)


def get_authenticated_user(request: Request) -> User:
    user = request.user
    if not isinstance(user, User):
        raise NotAuthenticated()
    return user


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["회원관리"],
        summary="내 정보 조회 API",
        responses={200: None},
    )
    def get(self, request: Request) -> Response:
        user = get_authenticated_user(request)
        return Response(UserProfileSerializer(user).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["회원관리"],
        summary="내 정보 수정 API",
        request=UserUpdateSerializer,
        responses={200: None},
    )
    def patch(self, request: Request) -> Response:
        user = get_authenticated_user(request)
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserProfileSerializer(user).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["회원관리"],
        summary="회원탈퇴 신청 API",
        request=OpenApiRequest(WithdrawalRequestSerializer),
        responses={204: None},
    )
    def delete(self, request: Request) -> Response:
        user = get_authenticated_user(request)
        serializer = WithdrawalRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        Withdrawal.objects.update_or_create(
            user=user,
            defaults={
                "reason": serializer.validated_data["reason"],
                "reason_detail": serializer.validated_data["reason_detail"],
                "due_date": timezone.now().date() + timedelta(days=getattr(settings, "WITHDRAWAL_GRACE_DAYS", 14)),
            },
        )
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class CheckNicknameAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["회원관리"],
        summary="닉네임 중복 조회 API",
        request=NicknameCheckSerializer,
        responses={200: None},
    )
    def post(self, request: Request) -> Response:
        serializer = NicknameCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nickname = serializer.validated_data["nickname"]
        if User.objects.filter(nickname__iexact=nickname).exists():
            return Response({"error_detail": "중복된 닉네임이 존재합니다."}, status=status.HTTP_409_CONFLICT)
        return Response({"detail": "사용가능한 닉네임 입니다."}, status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["회원관리"],
        summary="내 비밀번호 변경 API",
        request=ChangePasswordSerializer,
        responses={200: None},
    )
    def patch(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = get_authenticated_user(request)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return Response({"detail": "비밀번호가 변경되었습니다."}, status=status.HTTP_200_OK)


class ChangePhoneAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["회원관리"],
        summary="내 휴대폰 번호 변경 API",
        request=ChangePhoneSerializer,
        responses={200: None},
    )
    def patch(self, request: Request) -> Response:
        serializer = ChangePhoneSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = get_authenticated_user(request)
        serializer.update(user, serializer.validated_data)
        return Response({"phone_number": user.phone_number}, status=status.HTTP_200_OK)


class ProfileImageAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=["회원관리"],
        summary="프로필 사진 업로드 API",
        request=ProfileImageUploadSerializer,
        responses={200: None},
    )
    def patch(self, request: Request) -> Response:
        user = get_authenticated_user(request)
        serializer = ProfileImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        urls = ImageResizer().upload_square_resizes(
            image_file=serializer.validated_data["image"],
            sizes=(64, 128, 256),
            path_prefix=f"{USER_PROFILE_IMAGE_UPLOAD_PATH}{user.id}",
        )

        profile_url = urls.get("256", "")
        user.profile_image_url = profile_url or None
        user.save(update_fields=["profile_image_url", "updated_at"])
        return Response({"detail": "프로필 사진이 업데이트 되었습니다."}, status=status.HTTP_200_OK)

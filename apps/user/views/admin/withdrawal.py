from django.db import transaction
from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models.withdraw import Withdrawal
from apps.user.pagination import AdminAccountPagination
from apps.user.permissions import IsAdminStaffRole
from apps.user.serializers.admin.withdrawal import (
    AdminAccountWithdrawalListSerializer,
    AdminAccountWithdrawalRetrieveSerializer,
)

ROLE_QUERY_MAP: dict[str, str] = {
    "user": "U",
    "student": "ST",
    "training_assistant": "TA",
    "learning_coach": "LC",
    "operation_manager": "OM",
    "admin": "AD",
}


class AdminAccountWithdrawalListAPIView(APIView):

    permission_classes = [IsAdminStaffRole]

    @extend_schema(
        tags=["회원관리"],
        summary="회원탈퇴 요청 목록 조회 API",
        parameters=[
            OpenApiParameter("page", OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY),
            OpenApiParameter("page_size", OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY),
            OpenApiParameter("search", OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY),
            OpenApiParameter(
                "role",
                OpenApiTypes.STR,
                required=False,
                location=OpenApiParameter.QUERY,
                enum=list(ROLE_QUERY_MAP.keys()),
            ),
            OpenApiParameter(
                "sort",
                OpenApiTypes.STR,
                required=False,
                location=OpenApiParameter.QUERY,
                enum=["id", "latest", "oldest"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        withdrawal = Withdrawal.objects.select_related("user")

        search = request.query_params.get("search")
        if search:
            cond = Q(user__email__icontains=search) | Q(user__name__icontains=search)
            if search.isdigit():
                cond |= Q(id=int(search))
            withdrawal = withdrawal.filter(cond)

        role = request.query_params.get("role")
        if role:
            role_value = ROLE_QUERY_MAP.get(role)
            if role_value:
                withdrawal = withdrawal.filter(user__role=role_value)

        sort = request.query_params.get("sort")
        if sort == "latest":
            withdrawal = withdrawal.order_by("-created_at", "-id")
        elif sort == "oldest":
            withdrawal = withdrawal.order_by("created_at", "id")
        else:
            withdrawal = withdrawal.order_by("id")

        paginator = AdminAccountPagination()
        page = paginator.paginate_queryset(withdrawal, request, view=self)

        serializer = AdminAccountWithdrawalListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminAccountWithdrawalRetrieveDestroyAPIView(APIView):
    permission_classes = [IsAdminStaffRole]

    @extend_schema(
        tags=["회원관리"],
        summary="회원탈퇴 요청 상세 조회 API",
        responses={200: AdminAccountWithdrawalRetrieveSerializer},
    )
    def get(self, request: Request, withdrawal_id: int) -> Response:
        withdrawal = (
            Withdrawal.objects.select_related("user")
            .prefetch_related("user__cohortstudent_set__cohort__course")
            .filter(id=withdrawal_id)
            .first()
        )
        if withdrawal is None:
            return Response({"error_detail": "회원탈퇴 정보를 찾을 수 없습니다.."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminAccountWithdrawalRetrieveSerializer(withdrawal)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(tags=["회원관리"], summary="회원탈퇴 취소 API", responses={200: OpenApiTypes.OBJECT})
    def delete(self, request: Request, withdrawal_id: int) -> Response:
        withdrawal = Withdrawal.objects.select_related("user").filter(id=withdrawal_id).first()
        if withdrawal is None:
            return Response({"error_detail": "회원탈퇴 정보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        user = withdrawal.user

        with transaction.atomic():
            withdrawal.delete()
            user.is_active = True
            user.save(update_fields=["is_active"])

        return Response({"detail": "회원 탈퇴 취소처리 완료"}, status=status.HTTP_200_OK)

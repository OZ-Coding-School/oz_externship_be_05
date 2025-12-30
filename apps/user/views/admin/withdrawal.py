from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models.withdraw import Withdrawal
from apps.user.pagination import AdminAccountPagination
from apps.user.serializers.admin.withdrawal import (
    AdminAccountWithdrawalListSerializer,
    AdminAccountWithdrawalRetrieveSerializer,
)

STAFF_ROLES = {"TA", "LC", "OM", "AD"}

ROLE_QUERY_MAP: dict[str, str] = {
    "user": "U",
    "student": "ST",
    "training_assistant": "TA",
    "learning_coach": "LC",
    "operation_manager": "OM",
    "admin": "AD",
}


class AdminAccountWithdrawalListAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request: Request) -> Response:
        qs = Withdrawal.objects.select_related("user")

        search = request.query_params.get("search")
        if search:
            cond = Q(user__email__icontains=search) | Q(user__name__icontains=search)
            if search.isdigit():
                cond |= Q(id=int(search))
            qs = qs.filter(cond)

        role = request.query_params.get("role")
        if role:
            role_value = ROLE_QUERY_MAP.get(role)
            if role_value:
                qs = qs.filter(user__role=role_value)

        sort = request.query_params.get("sort")
        if sort == "latest":
            qs = qs.order_by("-created_at", "-id")
        elif sort == "oldest":
            qs = qs.order_by("created_at", "id")
        else:
            qs = qs.order_by("id")

        paginator = AdminAccountPagination()
        page = paginator.paginate_queryset(qs, request, view=self)

        serializer = AdminAccountWithdrawalListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminAccountWithdrawalRetrieveAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request: Request, withdrawal_id: int) -> Response:
        obj = (
            Withdrawal.objects.select_related("user")
            .prefetch_related("user__cohortstudent_set__cohort__course")
            .filter(id=withdrawal_id)
            .first()
        )
        if obj is None:
            return Response({"error_detail": "회원탈퇴 정보를 찾을 수 없습니다.."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminAccountWithdrawalRetrieveSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request: Request, withdrawal_id: int) -> Response:
        obj = Withdrawal.objects.select_related("user").filter(id=withdrawal_id).first()
        if obj is None:
            return Response({"error_detail": "회원탈퇴 정보를 찾을 수 없습니다.."}, status=status.HTTP_404_NOT_FOUND)

        user = obj.user
        obj.delete()

        if hasattr(user, "status"):
            try:
                user.status = "ACTIVATED"
                user.save(update_fields=["status"])
            except Exception:
                pass

        return Response({"detail":"회원 탈퇴 취소처리 완료"},status=status.HTTP_200_OK)
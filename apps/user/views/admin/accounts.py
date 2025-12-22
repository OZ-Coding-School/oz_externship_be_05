from django.db.models import Exists, OuterRef, Q
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models.user import RoleChoices, User
from apps.user.models.withdraw import Withdrawal
from apps.user.pagination import AdminAccountPagination
from apps.user.serializers.admin.accounts import AdminAccountListSerializer

STATUS_QUERY_VALUES = {"activated", "deactivated", "withdrew"}
ROLE_QUERY_VALUES = {"admin", "staff", "user", "student"}


ORDERING_MAP = {
    "id": "id",
    "created_at": "created_at",
    "birthday": "birthday",
}
ORDERING_ALLOWED = set(ORDERING_MAP.keys())
DIRECTION_ALLOWED = {"asc", "desc"}


class AdminAccountListAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request: Request) -> Response:
        qs = User.objects.all()

        qs = qs.annotate(is_withdrawing=Exists(Withdrawal.objects.filter(user_id=OuterRef("pk"))))

        search = request.query_params.get("search")
        if search:
            cond = Q(email__icontains=search) | Q(nickname__icontains=search) | Q(name__icontains=search)
            if search.isdigit():
                cond |= Q(id=int(search))
            qs = qs.filter(cond)

        status = request.query_params.get("status")
        if status:
            if status not in STATUS_QUERY_VALUES:
                raise ValidationError({"status": [f"invalid value. allowed: {sorted(STATUS_QUERY_VALUES)}"]})

            if status == "withdrew":
                qs = qs.filter(is_withdrawing=True)
            elif status == "activated":
                qs = qs.filter(is_withdrawing=False, is_active=True)
            elif status == "deactivated":
                qs = qs.filter(is_withdrawing=False, is_active=False)

        role = request.query_params.get("role")
        if role:
            if role not in ROLE_QUERY_VALUES:
                raise ValidationError({"role": [f"invalid value. allowed: {sorted(ROLE_QUERY_VALUES)}"]})

            if role == "admin":
                qs = qs.filter(role=RoleChoices.AD)
            elif role == "user":
                qs = qs.filter(role=RoleChoices.USER)
            elif role == "student":
                qs = qs.filter(role=RoleChoices.ST)
            elif role == "staff":
                qs = qs.filter(role__in=[RoleChoices.TA, RoleChoices.LC, RoleChoices.OM])

        ordering = (request.query_params.get("ordering") or "id").strip()
        direction = (request.query_params.get("direction") or "desc").strip()

        if ordering not in ORDERING_ALLOWED:
            raise ValidationError({"ordering": [f"invalid value. allowed: {sorted(ORDERING_ALLOWED)}"]})
        if direction not in DIRECTION_ALLOWED:
            raise ValidationError({"direction": [f"invalid value. allowed: {sorted(DIRECTION_ALLOWED)}"]})

        order_field = ORDERING_MAP[ordering]
        if direction == "desc":
            order_field = f"-{order_field}"
        qs = qs.order_by(order_field)

        paginator = AdminAccountPagination()
        page = paginator.paginate_queryset(qs, request, view=self)

        serializer = AdminAccountListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

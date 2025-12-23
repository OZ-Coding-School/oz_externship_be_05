from django.db.models import Exists, OuterRef, Q
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models.user import RoleChoices, User
from apps.user.models.withdraw import Withdrawal
from apps.user.pagination import AdminAccountPagination
from apps.user.serializers.admin.accounts import AdminAccountListSerializer


ORDERING_ALLOWED = {"id", "created_at", "birthday"}
DIRECTION_ALLOWED = {"asc", "desc"}

STATUS_FILTERS = {
    "withdrew" : Q(is_withdrawing=True),
    "activated" : Q(is_withdrawing=False, is_active=True),
    "deactivated" : Q(is_withdrawing=False, is_active=False),
}

ROLE_FILTERS = {
    "admin": Q(role=RoleChoices.AD),
    "user": Q(role=RoleChoices.USER),
    "student": Q(role=RoleChoices.ST),
    "staff": Q(role__in=[RoleChoices.TA, RoleChoices.LC, RoleChoices.OM])
}

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
        status_query = STATUS_FILTERS.get(status or "")
        if status_query:
            qs = qs.filter(status_query)

        role = request.query_params.get("role")
        role_query = ROLE_FILTERS.get(role or "")
        if role_query:
            qs = qs.filter(role_query)
            
        ordering = (request.query_params.get("ordering") or "id").strip()
        direction = (request.query_params.get("direction") or "desc").strip()

        if ordering not in ORDERING_ALLOWED:
            ordering = "id"
        if direction not in DIRECTION_ALLOWED:
            direction = "desc"

        order_field = ordering
        if direction == "desc":
            order_field = f"-{order_field}"
        qs = qs.order_by(order_field)

        paginator = AdminAccountPagination()
        page = paginator.paginate_queryset(qs, request, view=self)

        serializer = AdminAccountListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

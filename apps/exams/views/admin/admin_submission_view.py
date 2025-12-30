from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from rest_framework.generics import ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.utils.paginations import Pagination
from apps.exams.models import ExamSubmission
from apps.exams.permissions.admin_permission import AdminUserPermissionView
from apps.exams.serializers.admin.admin_submission_serializer import (
    AdminSubmissionListSerializer,
)
from apps.exams.services.admin.admin_submission_service import (
    build_admin_submission_query,
    parse_admin_submission_list_params,
)


class AdminSubmissionListAPIView(AdminUserPermissionView, ListAPIView):  # type: ignore[type-arg]
    serializer_class = AdminSubmissionListSerializer
    pagination_class = Pagination

    def get_queryset(self) -> QuerySet[ExamSubmission]:
        params = parse_admin_submission_list_params(self.request.query_params)
        return build_admin_submission_query(params)

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

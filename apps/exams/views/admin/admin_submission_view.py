from __future__ import annotations

from typing import Literal, cast

from rest_framework.request import Request
from rest_framework.response import Response

from apps.exams.permissions.admin_permission import AdminUserPermissionView
from apps.exams.serializers.admin.admin_submission_serializer import (
    AdminExamSubmissionListSerializer,
)
from apps.exams.services.admin.admin_submission_service import (
    AdminSubmissionListParams,
    get_admin_exam_submission_list,
)

Order = Literal["asc", "desc"]


class AdminSubmissionListAPIView(AdminUserPermissionView):
    def get(self, request: Request) -> Response:
        qp = request.query_params

        params = AdminSubmissionListParams(
            page=int(qp.get("page", 1)),
            size=int(qp.get("size", 10)),
            search_keyword=str(qp.get("search_keyword", "") or ""),
            cohort_id=int(qp["cohort_id"]) if qp.get("cohort_id") else None,
            exam_id=int(qp["exam_id"]) if qp.get("exam_id") else None,
            sort=str(qp.get("sort", "finished_at") or "finished_at"),
            order=cast(Order, qp.get("order") or "desc"),
        )

        payload = get_admin_exam_submission_list(params)

        ser = AdminExamSubmissionListSerializer(instance=payload)
        return Response(ser.data, status=200)

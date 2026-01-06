from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
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

    @extend_schema(
        tags=["쪽지시험 관리"],
        summary="쪽지시험 응시 내역 목록 조회",
        description=(
            "스태프(조교, 러닝 코치, 운영매니저) 및 관리자가 수강생들의 쪽지시험 응시 내역을 목록으로 조회합니다. 필터링, 검색, 정렬 및 페이지네이션 기능을 지원합니다."
        ),
        parameters=[
            OpenApiParameter("page", type=OpenApiTypes.INT, description="페이지 번호", default=1),
            OpenApiParameter("size", type=OpenApiTypes.INT, description="페이지당 항목 수", default=10),
            OpenApiParameter("search_keyword", type=OpenApiTypes.STR, description="검색어 (닉네임, 이름 등)"),
            OpenApiParameter("cohort_id", type=OpenApiTypes.INT, description="기수 ID 필터"),
            OpenApiParameter("exam_id", type=OpenApiTypes.INT, description="쪽지시험 ID 필터"),
            OpenApiParameter("sort", type=OpenApiTypes.STR, description="정렬 기준 (예: score, started_at)"),
            OpenApiParameter("order", type=OpenApiTypes.STR, description="정렬 순서 (asc, desc)", default="desc"),
        ],
        responses={
            200: AdminSubmissionListSerializer(many=False),  # Pagination 구조는 정의된 pagination_class를 따름
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "성공 응답 예시",
                value={
                    "count": 120,
                    "previous": None,
                    "next": "https://api.ozcodingschool.site/api/v1/admin/exams/submissions?page_size=10&page=2",
                    "results": [
                        {
                            "submission_id": 5501,
                            "nickname": "한율_회장",
                            "name": "한율",
                            "course_name": "초격차 백엔드 부트캠프",
                            "cohort_number": 14,
                            "exam_title": "Python 기본 문법 테스트",
                            "subject_name": "Python",
                            "score": 87,
                            "cheating_count": 0,
                            "started_at": "2025-03-01 10:03:12",
                            "finished_at": "2025-03-01 10:32:19",
                        }
                    ],
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[ExamSubmission]:
        params = parse_admin_submission_list_params(self.request.query_params)
        return build_admin_submission_query(params)

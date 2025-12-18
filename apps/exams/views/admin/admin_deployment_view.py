from typing import Any

from django.core.paginator import EmptyPage, Paginator
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.models import Cohort
from apps.exams.serializers.admin import (
    DeploymentListResponseSerializer,
    ErrorResponseSerializer,
)
from apps.exams.services.admin.admin_deployment_service import (
    list_admin_deployments,
)


class DeploymentListCreateAPIView(APIView):
    """
    GET - 배포 목록 조회
    POST - 배포 생성 (아직 구현 안 함)
    """

    # 권한 없으면 (403)
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="쪽지시험 배포 목록 조회 API",
        description=(
            "관리자가 배포된 쪽지시험 목록을 조회합니다. "
            "페이지네이션을 지원하며, 기수(cohort) 및 검색 키워드를 통해 "
            "배포 내역을 필터링할 수 있습니다."
        ),
        parameters=[
            OpenApiParameter("page", int, required=False),
            OpenApiParameter("size", int, required=False),
            OpenApiParameter("search_keyword", str, required=False),
            OpenApiParameter("cohort_id", int, required=False),
        ],
        responses={
            200: DeploymentListResponseSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=["쪽지시험 관리"],
    )
    def get(self, request: Any) -> Response:

        # page/size 검증 (400)
        try:
            page = int(request.query_params.get("page", 1))
            size = int(request.query_params.get("size", 10))
        except ValueError:
            raise ValidationError({"error_detail": "유효하지 않은 조회 요청입니다."})

        search_keyword = request.query_params.get("search_keyword")
        cohort_id = request.query_params.get("cohort_id")

        # cohort 검증 (400)
        cohort = None
        if cohort_id:
            try:
                cohort = Cohort.objects.get(pk=cohort_id)
            except Cohort.DoesNotExist:
                raise ValidationError({"error_detail": "유효하지 않은 조회 요청입니다."})

        qs = list_admin_deployments(cohort=cohort, search_keyword=search_keyword)

        # 조회 결과 자체가 없음 (404)
        if not qs.exists():
            raise NotFound({"error_detail": "등록된 배포 내역이 없습니다."})

        paginator = Paginator(qs, size)

        # page 범위 초과 (404)
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            raise NotFound({"error_detail": "등록된 배포 내역이 없습니다."})

        response_data = {
            "page": page,
            "size": size,
            "total_count": paginator.count,
            "deployments": [
                {
                    "deployment_id": d.id,
                    "exam_title": d.exam.title,
                    "subject_name": d.exam.subject.title,
                    "cohort_number": d.cohort.number,
                    "course_name": d.cohort.course.name,
                    "submit_count": getattr(d, "participant_count", 0),
                    "avg_score": round(getattr(d, "avg_score", 0.0) or 0.0, 1),
                    "status": d.status,
                    "created_at": d.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for d in page_obj
            ],
        }

        serializer = DeploymentListResponseSerializer(response_data)

        return Response(serializer.data)

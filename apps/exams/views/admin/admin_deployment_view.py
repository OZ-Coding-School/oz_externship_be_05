from django.db import IntegrityError
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.utils.paginations import Pagination
from apps.core.utils.types import to_int
from apps.exams.exceptions import DeploymentConflictException
from apps.exams.permissions.admin_permission import AdminUserPermission
from apps.exams.serializers.admin import (
    AdminDeploymentCreateResponseSerializer,
    AdminDeploymentListItemSerializer,
    AdminDeploymentListResponseSerializer,
    AdminDeploymentSerializer,
)
from apps.exams.services.admin.admin_deployment_service import (
    create_deployment,
    list_admin_deployments,
)


class DeploymentListCreateAPIView(AdminUserPermission):
    """
    GET - 배포 목록 조회
    POST - 배포 생성
    """

    # --------------------
    # GET - 배포 목록 조회
    # --------------------
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
            OpenApiParameter("subject_id", int, required=False),
            OpenApiParameter("cohort_id", int, required=False),
            OpenApiParameter(
                "sort",
                str,
                required=False,
                description="created_at | submit_count | avg_score",
            ),
            OpenApiParameter("order", str, required=False, description="asc | desc"),
        ],
        responses={
            200: AdminDeploymentListResponseSerializer,
            400: OpenApiResponse(description="유효하지 않은 요청입니다."),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="쪽지시험 배포 조회 권한이 없습니다."),
        },
        tags=["쪽지시험 관리"],
    )
    def get(self, request: Request) -> Response:

        # 쿼리셋 조회
        queryset = list_admin_deployments(
            cohort_id=to_int("cohort_id", request.query_params.get("cohort_id")),
            subject_id=to_int("subject_id", request.query_params.get("subject_id")),
            search_keyword=request.query_params.get("search_keyword"),
            sort=request.query_params.get("sort", "created_at"),
            order=request.query_params.get("order", "desc"),
        )

        paginator = Pagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AdminDeploymentListItemSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    # --------------------
    # POST - 배포 생성
    # --------------------
    @extend_schema(
        summary="쪽지시험 배포 생성 API",
        description="관리자가 새로운 쪽지시험 배포를 생성합니다.",
        request=AdminDeploymentSerializer,
        responses={
            201: OpenApiResponse(
                response=AdminDeploymentCreateResponseSerializer,
                description="쪽지시험 배포가 생성되었습니다.",
            ),
            400: OpenApiResponse(description="유효하지 않은 배포 생성 요청입니다."),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="쪽지시험 배포 생성 권한이 없습니다."),
            404: OpenApiResponse(description="배포 대상 과정-기수 또는 시험 정보를 찾을 수 없습니다."),
            409: OpenApiResponse(description="동일한 조건의 배포가 이미 존재합니다."),
        },
        tags=["쪽지시험 관리"],
    )
    def post(self, request: Request) -> Response:
        serializer = AdminDeploymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            deployment = create_deployment(
                cohort=serializer.validated_data["cohort"],
                exam=serializer.validated_data["exam"],
                duration_time=serializer.validated_data["duration_time"],
                open_at=serializer.validated_data["open_at"],
                close_at=serializer.validated_data["close_at"],
            )
        except IntegrityError:
            raise DeploymentConflictException(detail="이미 처리되었습니다.")

        return Response({"pk": deployment.pk}, status=status.HTTP_201_CREATED)

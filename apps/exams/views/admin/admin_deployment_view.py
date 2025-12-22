from typing import Any, cast

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.core.utils.ints import to_int
from apps.exams.permissions.admin_permission import IsStaffOrAdmin
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


class DeploymentListCreateAPIView(APIView):
    """
    GET - 배포 목록 조회
    POST - 배포 생성
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsStaffOrAdmin]

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

        # Pagination
        class _Pagination(PageNumberPagination):
            page_query_param = "page"
            page_size_query_param = "size"
            page_size = 10

            def get_paginated_response(self, data: Any) -> Response:
                size = self.get_page_size(cast(Request, self.request))

                if self.page is None:
                    return Response(
                        {
                            "page": 1,
                            "size": size or 10,
                            "total_count": 0,
                            "deployments": [],
                        },
                        status=status.HTTP_200_OK,
                    )

                return Response(
                    {
                        "page": self.page.number,
                        "size": size if size is not None else self.page.paginator.per_page,
                        "total_count": self.page.paginator.count,
                        "deployments": data,
                    },
                    status=status.HTTP_200_OK,
                )

        paginator = _Pagination()
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

        deployment, error_code = create_deployment(
            cohort=serializer.validated_data["cohort"],
            exam=serializer.validated_data["exam"],
            duration_time=serializer.validated_data["duration_time"],
            open_at=serializer.validated_data["open_at"],
            close_at=serializer.validated_data["close_at"],
        )

        # 에러 처리
        if error_code is not None:
            if error_code == "DUPLICATE":
                return Response(
                    {"detail": "동일한 조건의 배포가 이미 존재합니다."},
                    status=status.HTTP_409_CONFLICT,
                )
            elif error_code == "ALREADY_STARTED":
                return Response(
                    {"detail": "이미 시작된 시험입니다."},
                    status=status.HTTP_409_CONFLICT,
                )
            else:
                return Response(
                    {"detail": "배포 생성 실패"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # 정상 생성 시
        assert deployment is not None  # 타입 안정성 보장
        return Response(
            {
                "exam_id": deployment.exam_id,
                "cohort_id": deployment.cohort_id,
                "duration_time": deployment.duration_time,
                "access_code": deployment.access_code,
                "open_at": deployment.open_at,
                "close_at": deployment.close_at,
            },
            status=status.HTTP_201_CREATED,
        )

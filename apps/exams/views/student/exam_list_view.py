from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.utils.paginations import Pagination
from apps.exams.permissions.student_permission import StudentUserPermissionView
from apps.exams.serializers.student.exam_list_serializer import (
    ExamDeploymentListSerializer,
)
from apps.exams.services.student.exam_status_service import get_exam_deployment_queryset


class ExamDeploymentListView(StudentUserPermissionView):
    @extend_schema(
        tags=["쪽지시험"],
        summary="쪽지시험 목록 조회",
        description="수강생이 속한 기수의 쪽지시험 목록을 조회합니다.",
        responses={200: ExamDeploymentListSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:

        user = request.user
        # 파라미터 추출 및 검증
        filter_status = request.query_params.get("status")
        if filter_status not in ["done", "pending"]:
            return Response(
                {"error_detail": "올바르지 않은 status 파라미터입니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        # 기수 정보 확인
        queryset = get_exam_deployment_queryset(user, filter_status)

        if queryset is None:
            return Response({"error_detail": "사용자 정보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        # 페이지네이션 적용
        paginator = Pagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = ExamDeploymentListSerializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(serializer.data)

from __future__ import annotations

from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions.exception_messages import EMS
from apps.exams.models.exam_submission import ExamSubmission
from apps.exams.permissions.student_permission import (
    IsSubmissionOwner,
    StudentUserPermissionView,
)
from apps.exams.serializers.student.exam_result_serializer import ExamResultSerializer
from apps.exams.services.student.exam_result_service import (
    attach_exam_result_properties,
)


class ExamResultView(StudentUserPermissionView):
    """
    쪽지시험 결과 조회 API
    """

    # 인증된 사용자만 접근 가능
    permission_classes = StudentUserPermissionView.permission_classes + [IsSubmissionOwner]

    @extend_schema(
        tags=["쪽지시험"],
        summary="쪽지시험 결과 조회 API",
        responses={
            200: ExamResultSerializer,
        },
    )
    def get(
        self,
        request: Request,
        submission_id: int,
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        # submission_id로 시험 제출 내역 조회
        # deployment, exam을 함께 가져와 DB 조회 최소화
        try:
            submission = ExamSubmission.objects.select_related("deployment", "deployment__exam").get(pk=submission_id)
        except ExamSubmission.DoesNotExist:
            # 제출 내역이 없는 경우
            raise NotFound(detail=EMS.E404_NOT_FOUND("쪽지시험"))

        # 본인이 제출한 시험만 조회 가능
        self.check_object_permissions(request, submission)

        # 결과 조회용 응답 데이터 조립
        instance = attach_exam_result_properties(submission)

        # Serializer로 응답 형태 검증
        serializer = ExamResultSerializer(instance)

        # 결과 응답 반환
        return Response(serializer.data, status=200)

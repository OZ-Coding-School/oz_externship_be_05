from typing import Any

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions.exception_messages import EMS
from apps.exams.models.exam_submission import ExamSubmission
from apps.exams.permissions.student_permission import (
    IsSubmissionOwner,
    StudentUserPermission,
)
from apps.exams.serializers.student.exam_result_serializer import ExamResultSerializer
from apps.exams.services.student.exam_result_service import build_exam_result


class ExamResultView(StudentUserPermission):
    """
    쪽지시험 결과 확인 API
    """

    # 인증된 사용자만 접근 가능
    permission_classes = StudentUserPermission.permission_classes + [IsSubmissionOwner]

    @extend_schema(
        tags=["쪽지시험"],
        summary="쪽지시험 결과 확인 API",
        description="학생이 본인이 제출한 쪽지시험 결과를 조회합니다.",
        operation_id="exam_submission_result",
        responses={
            200: ExamResultSerializer,
            400: OpenApiResponse(description="유효하지 않은 시험 응시 세션입니다."),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="권한이 없습니다."),
            404: OpenApiResponse("해당 시험 정보를 찾을 수 없습니다."),
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
            submission = ExamSubmission.objects.select_related("deployment__exam").get(pk=submission_id)
        except ExamSubmission.DoesNotExist:
            # 제출 내역이 없는 경우
            raise NotFound(detail=EMS.E404_NOT_FOUND("쪽지시험"))

        # 본인이 제출한 시험만 조회 가능
        self.check_object_permissions(request, submission)

        if submission.started_at > submission.created_at:
            raise ValidationError(detail=EMS.E400_INVALID_SESSION("시험 응시"))

        # 결과 조회용 응답 데이터 조립
        data = build_exam_result(submission)

        # Serializer로 응답 형태 검증
        serializer = ExamResultSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        # 결과 응답 반환
        return Response(serializer.data, status=200)

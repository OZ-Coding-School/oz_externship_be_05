from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions.exception_messages import EMS
from apps.exams.models import ExamSubmission
from apps.exams.permissions.admin_permission import AdminUserPermissionView
from apps.exams.serializers.admin.admin_submission_detail_serializer import (
    ExamSubmissionDetailSerializer,
)
from apps.exams.services.admin.admin_submission_detail_services import (
    check_answer_correctness,
    normalize_answers,
)


class ExamAdminSubmissionDetailView(AdminUserPermissionView):
    """
    쪽지시험 응시 내역 상세 조회 API
    """

    @extend_schema(
        summary="쪽지시험 응시 내역 상세 조회 API",
        description="관리자가 특정 수강생의 쪽지시험 응시 내역을 상세 조회합니다.",
        responses={
            200: ExamSubmissionDetailSerializer,
            400: OpenApiResponse(
                description="유효하지 않은 상세 조회 요청입니다.",
                examples=[OpenApiExample(name="Bad Request", value=EMS.E400_INVALID_REQUEST("상세 조회"))],
            ),
            401: OpenApiResponse(
                description="인증 필요", examples=[OpenApiExample(name="Unauthorized", value=EMS.E401_NO_AUTH_DATA)]
            ),
            403: OpenApiResponse(
                description="권한 없음",
                examples=[OpenApiExample(name="Forbidden", value=EMS.E403_QUIZ_PERMISSION_DENIED("응시 상세 조회"))],
            ),
            404: OpenApiResponse(
                description="시험 정보 없음",
                examples=[OpenApiExample(name="Not Found", value=EMS.E404_NOT_FOUND("응시 내역"))],
            ),
        },
        tags=["쪽지시험 관리"],
    )
    def get(self, request: Request, submission_id: int) -> Response:
        """
        쪽지시험 응시 내역 상세 조회
        """

        try:
            submission = ExamSubmission.objects.select_related(
                "submitter", "deployment__exam__subject", "deployment__cohort__course"
            ).get(id=submission_id)

        except ExamSubmission.DoesNotExist:
            return Response(EMS.E404_NOT_FOUND("응시 내역"), status=status.HTTP_404_NOT_FOUND)

        # 채점 (기존 snapshot 활용)
        snapshot = submission.deployment.questions_snapshot

        try:
            answers = normalize_answers(submission.answers)
        except ValueError:
            return Response(EMS.E400_INVALID_REQUEST("응시 답안 형식"), status=status.HTTP_400_BAD_REQUEST)

        for idx, q in enumerate(snapshot, start=1):
            submitted = answers.get(str(q["question_id"]))
            q["number"] = idx
            q["submitted_answer"] = submitted
            q["is_correct"] = check_answer_correctness(submitted, q["answer"])

        serializer = ExamSubmissionDetailSerializer(submission, context={"questions_data": snapshot})

        return Response(serializer.data, status=status.HTTP_200_OK)

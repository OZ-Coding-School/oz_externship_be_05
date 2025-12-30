from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions.exception_messages import EMS
from apps.exams.models import ExamDeployment, ExamSubmission
from apps.exams.permissions.student_permission import StudentUserPermissionView
from apps.exams.serializers.student.exam_question_serializer import (
    ExamQuestionResponseSerializer,
)
from apps.exams.services.student.exam_question_service import (
    calculate_elapsed_time,
    validate_exam_access,
)


class ExamQuestionView(StudentUserPermissionView):
    """
    쪽지시험 응시 문제풀이 API
    """

    @extend_schema(
        summary="쪽지시험 응시 문제풀이 API",
        description="수강생이 쪽지시험 문제를 조회하고 풀이할 수 있습니다.",
        responses={
            200: ExamQuestionResponseSerializer,
            401: OpenApiResponse(
                description="Unauthorized - 인증되지 않음",
                examples=[
                    OpenApiExample(
                        name="인증 실패",
                        value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                    )
                ],
            ),
            403: OpenApiResponse(
                description="Forbidden - 권한 없음",
                examples=[
                    OpenApiExample(
                        name="학생 권한 없음",
                        value={"error_detail": "쪽지시험 조회 권한이 없습니다."},
                    )
                ],
            ),
            404: OpenApiResponse(
                description="Not Found - 배포 정보 없음",
                examples=[
                    OpenApiExample(
                        name="배포 없음",
                        value={"error_detail": "배포 정보를 찾을 수 없습니다."},
                    )
                ],
            ),
            410: OpenApiResponse(
                description="Gone - 시험 종료됨",
                examples=[
                    OpenApiExample(
                        name="시험 종료",
                        value={"error_detail": "시험이 종료되었습니다."},
                    )
                ],
            ),
            423: OpenApiResponse(
                description="Locked - 아직 응시 불가",
                examples=[
                    OpenApiExample(
                        name="응시 시간 아님",
                        value={"error_detail": "아직 응시할 수 없습니다."},
                    )
                ],
            ),
        },
        tags=["쪽지시험"],
    )
    def get(self, request: Request, deployment_id: int) -> Response:
        # 배포 정보 조회
        try:
            deployment = ExamDeployment.objects.select_related("exam").get(id=deployment_id)
        except ExamDeployment.DoesNotExist:
            raise NotFound(detail=EMS.E404_NOT_FOUND("배포 정보")["error_detail"])

        # 제출 내역 조회 (없을 수 있음)
        submission = ExamSubmission.objects.filter(deployment_id=deployment_id, submitter_id=request.user.id).first()

        # 시험 접근 가능 여부 검증 (서비스 레이어)
        validate_exam_access(deployment=deployment, submission=submission)

        # 문제 목록 조회 (스냅샷)
        questions = deployment.questions_snapshot

        # 각 문제에 번호 추가 및 정렬
        for idx, question in enumerate(questions, start=1):
            question["number"] = idx

        # 번호 순서대로 정렬
        questions_sorted = sorted(questions, key=lambda q: q["number"])

        # 경과 시간 계산 (서비스 레이어)
        elapsed_time = calculate_elapsed_time(submission=submission)

        # 부정행위 횟수
        cheating_count = submission.cheating_count if submission else 0

        # 응답 데이터 구성 (서비스 레이어)
        response_data = {
            "exam_id": deployment.exam_id,
            "exam_name": deployment.exam.title,
            "duration_time": deployment.duration_time,
            "elapsed_time": elapsed_time,
            "cheating_count": cheating_count,
            "questions": questions_sorted,
        }

        # 직렬화 및 응답
        serializer = ExamQuestionResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

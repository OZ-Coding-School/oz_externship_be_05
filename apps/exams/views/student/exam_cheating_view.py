from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions.exception_messages import EMS
from apps.core.exceptions.exceptions import GoneException
from apps.exams.models.exam_deployment import ExamDeployment
from apps.exams.models.exam_submission import ExamSubmission
from apps.exams.permissions.student_permission import StudentUserPermissionView
from apps.exams.serializers.student.exam_cheating_serializer import (
    ExamCheatingRequestSerializer,
    ExamCheatingResponseSerializer,
)
from apps.exams.services.student import exam_cheating_service

User = get_user_model()


class ExamCheatingCheckView(StudentUserPermissionView):
    """
    쪽지시험 부정행위 체크 API
    """

    @extend_schema(
        summary="쪽지시험 부정행위 체크 API",
        description="시험 응시 중 화면 이탈 등 부정행위 발생 시 카운트를 증가시킵니다. 3회 적발 시 자동으로 시험을 제출합니다.",
        tags=["쪽지시험"],
        request=ExamCheatingRequestSerializer,
        responses={
            200: OpenApiResponse(response=ExamCheatingResponseSerializer, description="부정행위 카운트 증가 성공"),
            400: OpenApiResponse(description="유효하지 않은 시험 응시 세션입니다."),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="권한이 없습니다."),
            404: OpenApiResponse(description="해당 시험 정보를 찾을 수 없습니다."),
            410: OpenApiResponse(description="시험이 이미 종료되었습니다."),
        },
    )
    def post(self, request: Request, deployment_id: int) -> Response:
        """
        부정행위 이벤트 발생 시 카운트 증가 및 강제 제출 처리
        """
        # 요청 데이터 검증
        serializer = ExamCheatingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Deployment 조회
        try:
            deployment = ExamDeployment.objects.get(pk=deployment_id)
        except ExamDeployment.DoesNotExist:
            return Response(EMS.E404_NOT_FOUND("쪽지시험"), status=status.HTTP_404_NOT_FOUND)

        # 시험 기간 유효성 검증
        if timezone.now() > deployment.close_at:
            raise GoneException(detail=EMS.E410_ALREADY_ENDED("쪽지시험")["error_detail"])

        # Submission 조회
        user = request.user
        if not isinstance(user, User):
            return Response(EMS.E401_NO_AUTH_DATA, status=status.HTTP_401_UNAUTHORIZED)

        try:
            submission = ExamSubmission.objects.get(deployment_id=deployment_id, submitter=user)
        except ExamSubmission.DoesNotExist:
            return Response(EMS.E400_INVALID_SESSION("시험 응시"), status=status.HTTP_400_BAD_REQUEST)

        # 서비스 레이어에서 비즈니스 로직 처리
        result = exam_cheating_service.handle_cheating_event(submission=submission, deployment=deployment)

        # 응답 직렬화 및 반환
        response_serializer = ExamCheatingResponseSerializer(data=result)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=status.HTTP_200_OK)

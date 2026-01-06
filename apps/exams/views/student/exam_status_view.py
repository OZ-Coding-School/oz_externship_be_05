from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions.exception_messages import EMS
from apps.exams.models import ExamDeployment
from apps.exams.models.exam_deployment import DeploymentStatus
from apps.exams.permissions.student_permission import StudentUserPermissionView
from apps.exams.services.student.exam_status_service import get_student_exam_status


class ExamDeploymentStatusCheckView(StudentUserPermissionView):
    """
    학생용 쪽지시험 상태 확인 API
    """

    @extend_schema(
        summary="쪽지시험 상태 확인 API",
        description="수강생이 시험 페이지에서 쪽지시험 상태를 주기적으로 확인합니다.",
        responses={
            200: OpenApiResponse(
                description="시험 상태 조회 성공",
                examples=[
                    OpenApiExample(
                        name="시험 진행중", value={"exam_status": DeploymentStatus.ACTIVATED, "force_submit": False}
                    ),
                    OpenApiExample(
                        name="시험 종료", value={"exam_status": DeploymentStatus.DEACTIVATED, "force_submit": True}
                    ),
                ],
            ),
            400: OpenApiResponse(
                description="유효하지 않은 시험 응시 세션입니다.",
                examples=[OpenApiExample(name="Bad Request", value=EMS.E400_INVALID_SESSION("시험"))],
            ),
            401: OpenApiResponse(
                description="인증 필요", examples=[OpenApiExample(name="Unauthorized", value=EMS.E401_NO_AUTH_DATA)]
            ),
            403: OpenApiResponse(
                description="권한 없음",
                examples=[OpenApiExample(name="Forbidden", value=EMS.E403_QUIZ_PERMISSION_DENIED("조회"))],
            ),
            404: OpenApiResponse(
                description="시험 정보 없음",
                examples=[OpenApiExample(name="Not Found", value=EMS.E404_NOT_FOUND("시험"))],
            ),
            410: OpenApiResponse(
                description="시험 종료됨", examples=[OpenApiExample(name="Gone", value=EMS.E410_ALREADY_ENDED("시험"))]
            ),
        },
        tags=["쪽지시험"],
    )
    def get(self, request: Request, deployment_id: int) -> Response:
        try:
            deployment = ExamDeployment.objects.get(id=deployment_id)
        except ExamDeployment.DoesNotExist:
            raise NotFound(detail=EMS.E404_NOT_FOUND("시험"))

        status_info = get_student_exam_status(deployment)
        return Response(status_info, status=status.HTTP_200_OK)

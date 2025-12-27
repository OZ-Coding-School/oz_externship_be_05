from typing import Any

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.request import Request
from rest_framework.response import Response

from apps.exams.models.exam_deployment import ExamDeployment
from apps.exams.permissions.student_permission import StudentUserPermission
from apps.exams.serializers.student.exam_submit_serializer import (
    ExamSubmissionCreateSerializer,
)


@extend_schema(
    tags=["쪽지시험"],
    summary="쪽지시험 제출 API",
    description=(
        "수강생이 쪽지시험 문제 풀이를 제출하는 API\n\n"
        "- 제출 시 각 문항별 답안, 부정행위 횟수, 시험 시작 시간이 함께 저장되며 "
        "자동 채점 후 결과를 반환합니다."
    ),
    operation_id="exam_submit",
    request=ExamSubmissionCreateSerializer,
    responses={
        201: OpenApiResponse(
            description="시험 제출 성공",
            response={
                "type": "object",
                "properties": {
                    "submission_id": {"type": "integer"},
                    "score": {"type": "integer"},
                    "correct_answer_count": {"type": "integer"},
                    "redirect_url": {"type": "string", "format": "uri"},
                },
                "required": ["submission_id", "score", "correct_answer_count", "redirect_url"],
            },
        ),
        400: OpenApiResponse(description="유효하지 않은 시험 응시 세션입니다."),
        401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
        403: OpenApiResponse(description="권한이 없습니다."),
        404: OpenApiResponse(description="해당 시험 정보를 찾을 수 없습니다."),
        409: OpenApiResponse(description="이미 제출된 시험입니다."),
    },
)
class ExamSubmissionCreateAPIView(StudentUserPermission):

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        deployment_id = request.data.get("deployment_id")
        deployment = get_object_or_404(ExamDeployment, pk=deployment_id)

        serializer = ExamSubmissionCreateSerializer(
            data=request.data, context={"request": request, "deployment": deployment}
        )
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()

        return Response(serializer.to_representation(submission), status=201)

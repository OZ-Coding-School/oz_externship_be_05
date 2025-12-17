from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.exams.models.exam_deployment import ExamDeployment
from apps.exams.serializers.student.exam_submit_serializer import (
    ExamSubmissionCreateSerializer,
)


@extend_schema(
    tags=["Exams - Student"],
    summary="쪽지시험 제출 API",
    description=(
        "수강생이 쪽지시험 문제 풀이를 제출하는 API.\n"
        "제출 시 각 문항별 답안, 부정행위 횟수, 시험 시작 시간이 함께 저장되며 "
        "자동 채점 후 결과를 반환합니다."
    ),
    operation_id="exam_submit",
)
class ExamSubmissionCreateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, deployment_pk: int) -> Response:
        try:
            deployment = ExamDeployment.objects.get(pk=deployment_pk)
        except ExamDeployment.DoesNotExist:
            return Response({"error_detail": "해당시험을 찾을 수 없음"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ExamSubmissionCreateSerializer(
            data=request.data,
            context={
                "request": request,
                "deployment": deployment,
            },
        )
        serializer.is_valid(raise_exception=True)

        try:
            submission = serializer.save(submitter=request.user, deployment=deployment)
        except ValueError as e:
            detail = str(e)

            if isinstance(detail, str):
                msg = detail
                if "2회" in msg:
                    return Response({"error_detail": msg}, status=status.HTTP_409_CONFLICT)
                if "error_detail" in detail:
                    return Response(detail, status=status.HTTP_400_BAD_REQUEST)

                raise

        return Response(serializer.to_representation(submission), status=201)

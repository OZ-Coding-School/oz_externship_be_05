from __future__ import annotations

from typing import cast

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request

from apps.exams.permissions.student_permission import StudentUserPermissionView
from apps.exams.serializers.student.exam_submit_serializer import (
    ExamSubmissionCreateSerializer,
)
from apps.exams.services.student.exam_submit_service import (
    create_exam_submission,
    validate_exam_submission_limit,
    validate_exam_total_seconds,
    validate_submission_time_limit,
)
from apps.user.models import User


@extend_schema(
    tags=["쪽지시험"],
    summary="쪽지시험 제출 API",
    description=(
        "수강생이 쪽지시험 문제 풀이를 제출하는 API.\n"
        "제출 시 각 문항별 답안, 부정행위 횟수, 시험 시작 시간이 함께 저장되며 "
        "자동 채점 후 결과를 반환합니다."
    ),
    operation_id="exam_submit",
)
class ExamSubmissionCreateAPIView(StudentUserPermissionView):
    def post(self, request: Request) -> HttpResponseRedirect:
        serializer = ExamSubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validate_submission_time_limit(deployment=serializer.validated_data["deployment"])
        validate_exam_submission_limit(
            deployment=serializer.validated_data["deployment"], submitter=cast(User, request.user)
        )
        validate_exam_total_seconds(
            deployment=serializer.validated_data["deployment"], started_at=serializer.validated_data["started_at"]
        )
        instance = create_exam_submission(submitter=cast(User, request.user), **serializer.validated_data)

        return redirect(f"{settings.FRONTEND_DOMAIN}/exams/submissions/{instance.pk}")

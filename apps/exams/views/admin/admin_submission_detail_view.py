from django.db import IntegrityError, transaction
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions.exception_messages import EMS
from apps.exams.models import ExamSubmission
from apps.exams.permissions.admin_permission import (
    AdminUserPermissionView,
    IsStaffOrAdmin,
)
from apps.exams.serializers.admin.admin_submission_detail_serializer import (
    ExamSubmissionDetailSerializer,
)
from apps.exams.services.admin.admin_submission_detail_services import (
    get_merged_submission_detail,
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

        detail_data = get_merged_submission_detail(submission)

        serializer = ExamSubmissionDetailSerializer(detail_data)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="쪽지시험 응시 내역 삭제 API",
        description="관리자가 특정 수강생의 쪽지시험 응시 내역을 삭제합니다.",
        responses={
            200: OpenApiResponse(
                description="삭제 성공",
                examples=[OpenApiExample(name="OK", value={"submission_id": 5501})],
            ),
            400: OpenApiResponse(
                description="유효하지 않은 응시 내역 삭제 요청입니다.",
                examples=[OpenApiExample(name="Bad Request", value=EMS.E400_INVALID_REQUEST("응시 내역 삭제"))],
            ),
            401: OpenApiResponse(
                description="인증 필요",
                examples=[OpenApiExample(name="Unauthorized", value=EMS.E401_NO_AUTH_DATA)],
            ),
            403: OpenApiResponse(
                description="권한 없음",
                examples=[
                    OpenApiExample(name="Forbidden", value={"error_detail": "쪽지시험 응시 내역 삭제 권한이 없습니다."})
                ],
            ),
            404: OpenApiResponse(
                description="삭제할 응시 내역을 찾을 수 없습니다.",
                examples=[OpenApiExample(name="Not Found", value=EMS.E404_NOT_FOUND("응시 내역"))],
            ),
            409: OpenApiResponse(
                description="충돌",
                examples=[
                    OpenApiExample(
                        name="Conflict", value={"error_detail": "응시 내역 삭제 처리 중 충돌이 발생했습니다."}
                    )
                ],
            ),
        },
        tags=["쪽지시험 관리"],
    )
    def delete(self, request: Request, submission_id: int) -> Response:
        if not IsStaffOrAdmin().has_permission(request, self):
            raise PermissionDenied(detail="쪽지시험 응시 내역 삭제 권한이 없습니다.")

        # 400
        if submission_id <= 0:
            return Response(
                EMS.E400_INVALID_REQUEST("응시 내역 삭제"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 404
        try:
            submission = ExamSubmission.objects.get(id=submission_id)
        except ExamSubmission.DoesNotExist:
            return Response(EMS.E404_NOT_FOUND("응시 내역"), status=status.HTTP_404_NOT_FOUND)

        # 409
        try:
            with transaction.atomic():
                submission.delete()
        except IntegrityError:
            return Response(
                {"error_detail": "응시 내역 삭제 처리 중 충돌이 발생했습니다."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response({"submission_id": submission_id}, status=status.HTTP_200_OK)

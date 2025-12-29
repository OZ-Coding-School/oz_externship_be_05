from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from apps.exams.permissions.student_permission import StudentUserPermissionView
from apps.exams.serializers.student.exam_access_serializer import (
    ExamAccessCodeSerializer,
)
from apps.exams.services.student.exam_access_service import ExamAccessCodeService


class ExamAccessCodeVerifyView(StudentUserPermissionView):
    """
    쪽지시험 참가 코드 검증 API
    """

    @extend_schema(
        summary="쪽지시험 참가 코드 검증",
        description="Base62로 인코딩된 참가 코드를 검증합니다.",
        request=ExamAccessCodeSerializer,
        responses={
            204: OpenApiResponse(description="No Content - 코드 검증 성공"),
            400: OpenApiResponse(
                description="Bad Request - 코드 불일치 또는 유효하지 않은 요청",
                examples=[
                    OpenApiExample(name="코드 불일치", value={"error_detail": "응시 코드가 일치하지 않습니다."}),
                    OpenApiExample(
                        name="필수 필드 누락", value={"error_detail": {"code": "이 필드는 필수 항목입니다."}}
                    ),
                ],
            ),
            401: OpenApiResponse(
                description="Unauthorized - 인증되지 않음",
                examples=[
                    OpenApiExample(name="인증 실패", value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."})
                ],
            ),
            403: OpenApiResponse(
                description="Forbidden - 권한 없음",
                examples=[
                    OpenApiExample(name="학생 권한 없음", value={"error_detail": "시험에 응시할 권한이 없습니다."})
                ],
            ),
            404: OpenApiResponse(
                description="Not Found - 배포 정보 없음",
                examples=[OpenApiExample(name="배포 없음", value={"error_detail": "배포 정보를 찾을 수 없습니다."})],
            ),
            423: OpenApiResponse(
                description="Locked - 아직 응시 불가",
                examples=[OpenApiExample(name="응시 시간 아님", value={"error_detail": "아직 응시할 수 없습니다."})],
            ),
        },
        tags=["쪽지시험"],
    )
    def post(self, request: Request, deployment_id: int) -> Response:
        # 요청 데이터 검증
        serializer = ExamAccessCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # 서비스 레이어에서 비즈니스 로직 처리
            ExamAccessCodeService.verify_access_code(
                deployment_id=deployment_id, access_code=serializer.validated_data["code"]
            )
        except ValidationError as e:
            message = e.detail[0] if isinstance(e.detail, list) else str(e.detail)
            return Response(
                {"error_detail": str(message)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

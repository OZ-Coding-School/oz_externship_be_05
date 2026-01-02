import uuid
from typing import cast

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.utils.s3_client import S3Client
from apps.qna.serializers.answer.images import AnswerImagePresignedURLSerializer
from apps.qna.views.answer.base import BaseAnswerAPIView


@extend_schema_view(
    post=extend_schema(
        summary="이미지 업로드용 Presigned URL 발급",
        tags=["질의응답"],
        description="S3에 이미지를 직접 업로드하기 위한 임시 URL을 발급합니다.",
        request=AnswerImagePresignedURLSerializer,
    )
)
class AnswerImagePresignedURLView(BaseAnswerAPIView):
    def post(self, request: Request, question_id: int, answer_id: int) -> Response:
        serializer = AnswerImagePresignedURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_name = cast(str, serializer.validated_data["file_name"])
        ext = file_name.split(".")[-1] if "." in file_name else "bin"
        s3_key = f"answer_images/{uuid.uuid4()}.{ext}"

        try:
            client = S3Client()
            presigned_url = client.generate_presigned_url(
                key=s3_key,
                expires_in=3600,
            )
            return Response(
                {
                    "url": presigned_url,
                    "image_key": s3_key,
                    "file_name": file_name,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

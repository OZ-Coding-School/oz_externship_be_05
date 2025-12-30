import uuid

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.constants import QUESTION_IMAGE_UPLOAD_PATH
from apps.core.utils.s3_client import S3Client
from apps.qna.serializers.question.question_images import PresignedUploadSerializer


class PresignedUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    @extend_schema(
        tags=["질의응답"],
        summary="질문 이미지 API",
        request=PresignedUploadSerializer,
    )
    def post(self, request: Request) -> Response:
        serializer = PresignedUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        original_name = serializer.validated_data["file_name"]

        ext = original_name.split(".")[-1].lower() if "." in original_name else ""
        if ext not in self.ALLOWED_EXTENSIONS:
            return Response(
                {"error": f"지원하지 않는 파일 형식입니다. ({', '.join(self.ALLOWED_EXTENSIONS)} 만 가능)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_filename = f"{uuid.uuid4()}.{ext}"

        # constants.py 의 질문경로 추가
        path_prefix = QUESTION_IMAGE_UPLOAD_PATH
        key = f"{path_prefix}{new_filename}"

        try:
            s3_client = S3Client()
            presigned_url = s3_client.generate_presigned_url(key=key)
            full_url = s3_client.build_url(key=key)

            return Response(
                {"presigned_url": presigned_url, "img_url": full_url, "key": key}, status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

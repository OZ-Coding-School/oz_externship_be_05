import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.core.utils.s3_client import S3Client

from apps.core.constants import QUESTION_IMAGE_UPLOAD_PATH, ANSWER_IMAGE_UPLOAD_PATH
from apps.qna.serializers.common.presigned_url_serializer import PresignedUploadSerializer


class PresignedUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    @extend_schema(request=PresignedUploadSerializer)
    def post(self, request):
        # 1. 시리얼라이저로 데이터 받기 및 검증
        serializer = PresignedUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. 검증된 데이터 꺼내기 (validated_data 사용)
        original_name = serializer.validated_data['file_name']
        upload_type = serializer.validated_data['upload_type']

        # 3. 확장자 검증 (로직 동일)
        ext = original_name.split(".")[-1].lower() if "." in original_name else ""
        if ext not in self.ALLOWED_EXTENSIONS:
            return Response(
                {"error": f"지원하지 않는 파일 형식입니다. ({', '.join(self.ALLOWED_EXTENSIONS)} 만 가능)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_filename = f"{uuid.uuid4()}.{ext}"

        # 4. 경로 결정
        if upload_type == "answer":
            path_prefix = ANSWER_IMAGE_UPLOAD_PATH
        else:
            path_prefix = QUESTION_IMAGE_UPLOAD_PATH

        key = f"{path_prefix}{new_filename}"

        try:
            s3_client = S3Client()
            presigned_url = s3_client.generate_presigned_url(key=key)
            full_url = s3_client.get_url(key)

            return Response({
                "presigned_url": presigned_url,
                "img_url": full_url,
                "key": key
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
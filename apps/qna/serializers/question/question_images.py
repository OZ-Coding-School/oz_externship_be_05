from typing import Any

from rest_framework import serializers

from apps.core.utils.s3_client import S3Client
from apps.qna.models import QuestionImage


# 1. 업로드 요청 검증용
class PresignedUploadSerializer(serializers.Serializer[Any]):
    file_name = serializers.CharField(max_length=255)


# 2. 이미지 조회/응답용
class QuestionImageSerializer(serializers.ModelSerializer[QuestionImage]):
    img_url = serializers.SerializerMethodField()

    class Meta:
        model = QuestionImage
        fields = ["id", "img_url"]

    def get_img_url(self, obj: QuestionImage) -> str:
        if not obj.img_url:
            return ""

        # 이미 Full URL이면 그대로 반환
        if obj.img_url.startswith("http"):
            return str(obj.img_url)

        return S3Client().build_url(obj.img_url)

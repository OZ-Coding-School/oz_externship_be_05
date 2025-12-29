from typing import Any

from rest_framework import serializers

from apps.qna.models.answer.images import AnswerImage

from apps.core.utils.s3_client import S3Client

class AnswerImageSerializer(serializers.ModelSerializer[AnswerImage]):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = AnswerImage
        fields = ["id", "image_url"]

    def get_image_url(self, obj: AnswerImage) -> str:
        return S3Client().build_url(obj.image_url)

class AnswerImagePresignedURLSerializer(serializers.Serializer[Any]):
    file_name = serializers.CharField(
        help_text="업로드할 파일명 (확장자 포함, 예: image.jpg)",
        required=True,
        max_length=255,
    )

    def validate_file_name(self, value: str) -> str:
        valid_image_extensions = {"png", "jpg", "jpeg", "gif", "webp"}

        if "." not in value:
            raise serializers.ValidationError("확장자가 포함된 파일명을 입력해주세요.")

        ext = value.split(".")[-1].lower()

        if ext not in valid_image_extensions:
            allowed_exts = ", ".join(sorted(valid_image_extensions))
            raise serializers.ValidationError(f"지원하지 않는 파일 형식입니다. ({allowed_exts}만 가능)")

        return value

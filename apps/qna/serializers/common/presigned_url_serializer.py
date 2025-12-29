from rest_framework import serializers

class PresignedUploadSerializer(serializers.Serializer):
    file_name = serializers.CharField(required=True, help_text="확장자를 포함한 파일명 (예: image.jpg)")
    upload_type = serializers.ChoiceField(
        choices=["question", "answer"],
        default="question",
        help_text="업로드 대상 (question 또는 answer)"
    )
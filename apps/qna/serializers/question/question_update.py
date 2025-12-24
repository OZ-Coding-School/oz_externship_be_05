from rest_framework import serializers

from apps.qna.models import Question, QuestionCategory

from .question_image_update import QuestionImagePatchSerializer


class QuestionUpdateSerializer(serializers.Serializer[Question]):
    title = serializers.CharField(required=False)
    content = serializers.CharField(required=False)
    category = serializers.PrimaryKeyRelatedField(
        queryset=QuestionCategory.objects.all(),
        required=False,
    )
    images = QuestionImagePatchSerializer(required=False)

from rest_framework import serializers

from apps.qna.models import QuestionImage


class QuestionImagePatchSerializer(serializers.Serializer[QuestionImage]):
    delete_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
    )
    add_urls = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        default=list,
    )

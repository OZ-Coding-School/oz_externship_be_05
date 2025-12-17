from rest_framework import serializers


class QuestionListSpecSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    category = serializers.DictField(child=serializers.CharField())
    author = serializers.DictField(child=serializers.CharField(allow_null=True))

    title = serializers.CharField()
    content_preview = serializers.CharField()

    answer_count = serializers.IntegerField()
    view_count = serializers.IntegerField()

    thumbnail_image_url = serializers.URLField(allow_null=True, required=False)

    created_at = serializers.DateTimeField()

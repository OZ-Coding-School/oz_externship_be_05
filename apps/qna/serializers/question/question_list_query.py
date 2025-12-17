from rest_framework import serializers


class QuestionListQuerySerializer(serializers.Serializer): # type: ignore[type-arg]
    answered = serializers.BooleanField(required=False)
    category = serializers.IntegerField(required=False, min_value=1)
    search = serializers.CharField(required=False, allow_blank=True)

    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=50, default=10)

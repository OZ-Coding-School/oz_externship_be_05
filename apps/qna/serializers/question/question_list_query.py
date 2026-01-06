from rest_framework import serializers


class QuestionListQuerySerializer(serializers.Serializer[dict[str, object]]):
    search_keyword = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.IntegerField(required=False)

    answer_status = serializers.CharField(required=False)
    sort = serializers.CharField(required=False, default="latest")

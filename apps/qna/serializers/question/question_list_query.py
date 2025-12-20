from rest_framework import serializers


class QuestionListQuerySerializer(serializers.Serializer[dict[str, object]]):
    page = serializers.IntegerField(min_value=1, default=1)
    size = serializers.IntegerField(min_value=1, max_value=50, default=10)

    search_keyword = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.IntegerField(required=False, min_value=1)

    answer_status = serializers.ChoiceField(
        choices=["answered", "unanswered"],
        required=False,
    )

    sort = serializers.ChoiceField(
        choices=["latest", "oldest", "views"],
        required=False,
        default="latest",
    )

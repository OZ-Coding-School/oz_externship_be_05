from typing import Any, Dict, List, cast

from rest_framework import serializers

from apps.qna.models.answer.answers import Answer
from apps.qna.serializers.answer.author import AnswerAuthorSerializer
from apps.qna.serializers.answer.comments import AnswerCommentSerializer
from apps.qna.serializers.answer.images import AnswerImageSerializer


class AnswerSerializer(serializers.ModelSerializer[Answer]):
    author = AnswerAuthorSerializer(read_only=True)
    images = AnswerImageSerializer(many=True, read_only=True)

    preview_comments = serializers.SerializerMethodField()
    total_comments_count = serializers.IntegerField(
        source="comments.count",
        read_only=True,
    )

    class Meta:
        model = Answer
        fields = [
            "id",
            "author",
            "content",
            "images",
            "is_adopted",
            "created_at",
            "preview_comments",
            "total_comments_count",
        ]
        read_only_fields = ["is_adopted", "created_at"]

    def get_preview_comments(self, obj: Answer) -> List[Dict[str, Any]]:
        comments = obj.comments.all()[:3]
        data = AnswerCommentSerializer(comments, many=True).data
        return cast(List[Dict[str, Any]], data)


class AnswerInputSerializer(serializers.ModelSerializer[Answer]):
    image_urls = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        write_only=True,
        help_text="본문에 포함된 이미지 URL 리스트",
    )

    class Meta:
        model = Answer
        fields = ["content", "image_urls"]


class AnswerAdoptRequestSerializer(serializers.Serializer[Any]):
    question_id = serializers.IntegerField()
    answer_id = serializers.IntegerField()
    is_adopted = serializers.BooleanField()


class AnswerCreateResponseSerializer(serializers.Serializer[Any]):
    answer_id = serializers.IntegerField(source="id")
    question_id = serializers.IntegerField(source="question.id")
    author_id = serializers.IntegerField(source="author.id")
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")


class AnswerUpdateResponseSerializer(serializers.Serializer[Any]):
    answer_id = serializers.IntegerField(source="id")
    updated_at = serializers.DateTimeField(
        source="modified_at",
        format="%Y-%m-%d %H:%M:%S",
    )


class AnswerAdoptResponseSerializer(serializers.Serializer[Any]):
    question_id = serializers.IntegerField(source="question.id")
    answer_id = serializers.IntegerField(source="id")
    is_adopted = serializers.BooleanField()


class AdminAnswerDeleteResponseSerializer(serializers.Serializer[Any]):
    answer_id = serializers.IntegerField()
    deleted_comment_count = serializers.IntegerField()

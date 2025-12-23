from typing import Any

from rest_framework import serializers

from apps.qna.models.answer.comments import AnswerComment
from apps.qna.serializers.answer.author import AnswerAuthorSerializer


class AnswerCommentSerializer(serializers.ModelSerializer[AnswerComment]):
    author = AnswerAuthorSerializer(read_only=True)

    class Meta:
        model = AnswerComment
        fields = ["id", "author", "content", "created_at"]
        read_only_fields = ["created_at"]


class CommentCreateResponseSerializer(serializers.Serializer[Any]):
    comment_id = serializers.IntegerField(source="id")
    answer_id = serializers.IntegerField(source="answer.id")
    author_id = serializers.IntegerField(source="author.id")
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

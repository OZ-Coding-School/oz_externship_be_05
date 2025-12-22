from rest_framework import serializers

from apps.qna.models import Answer, AnswerComment, Question
from apps.qna.serializers.common.author_serializer import AuthorSerializer
from apps.qna.services.question.question_list.category_utils import (
    CategoryInfo,
    build_category_info,
)


class AnswerCommentSerializer(serializers.ModelSerializer[AnswerComment]):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = AnswerComment
        fields = [
            "id",
            "content",
            "created_at",
            "author",
        ]


class AnswerSerializer(serializers.ModelSerializer[Answer]):
    author = AuthorSerializer(read_only=True)
    comments = AnswerCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Answer
        fields = [
            "id",
            "content",
            "created_at",
            "is_adopted",
            "author",
            "comments",
        ]


class QuestionDetailSerializer(serializers.ModelSerializer[Question]):
    category = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    author = AuthorSerializer(read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "content",
            "category",
            "images",
            "view_count",
            "created_at",
            "author",
            "answers",
        ]

    def get_images(self, obj: Question) -> list[str]:
        return [img.img_url for img in obj.images.all()]

    def get_category(self, obj: Question) -> CategoryInfo:
        return build_category_info(obj.category)

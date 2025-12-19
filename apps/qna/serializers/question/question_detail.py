from rest_framework import serializers

from apps.qna.models import Question
from apps.qna.services.question.question_list.category_utils import build_category_path


class AuthorSerializer(serializers.Serializer):  # type: ignore[type-arg]
    nickname = serializers.CharField()
    profile_img_url = serializers.CharField(source="profile_image_url", allow_null=True)


class AnswerCommentSerializer(serializers.Serializer):  # type: ignore[type-arg]
    comment_id = serializers.IntegerField(source="id")
    content = serializers.CharField()
    created_at = serializers.DateTimeField()
    author = AuthorSerializer()


class AnswerSerializer(serializers.Serializer):  # type: ignore[type-arg]
    answer_id = serializers.IntegerField(source="id")
    content = serializers.CharField()
    created_at = serializers.DateTimeField()
    is_adopted = serializers.BooleanField()
    author = AuthorSerializer()
    comments = AnswerCommentSerializer(source="answer_comments", many=True)


class QuestionDetailSerializer(serializers.Serializer):  # type: ignore[type-arg]
    question_id = serializers.IntegerField(source="id")
    title = serializers.CharField()
    content = serializers.CharField()
    images = serializers.SerializerMethodField()
    category_path = serializers.SerializerMethodField()
    view_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    author = AuthorSerializer()
    answers = AnswerSerializer(many=True)

    def get_images(self, obj: Question) -> list[str]:
        return [img.img_url for img in obj.images.all()]

    def get_category_path(self, obj: Question) -> str:
        return build_category_path(obj.category)["path"]

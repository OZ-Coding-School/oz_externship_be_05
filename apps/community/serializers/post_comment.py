from rest_framework import serializers

from apps.community.models.post_comment import PostComment
from apps.community.models.post_comment_tags import PostCommentTag
from apps.user.models import User


class AuthorSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["id", "nickname", "profile_image_url"]
        read_only_fields = ["id", "nickname", "profile_image_url"]


class TaggedUserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["id", "nickname"]
        read_only_fields = ["id", "nickname"]


class PostCommentTagsSerializer(serializers.ModelSerializer[PostCommentTag]):
    tagged_user = TaggedUserSerializer()

    class Meta:
        model = PostCommentTag
        fields = ["tagged_user"]


class PostCommentSerializer(serializers.ModelSerializer[PostComment]):
    author = AuthorSerializer(read_only=True)
    tagged_users = PostCommentTagsSerializer(source="postcommenttag_set", many=True, required=False)
    content = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            "required": "이 필드는 필수 항목입니다.",
            "blank": "이 필드는 필수 항목입니다.",
        },
    )

    class Meta:
        model = PostComment
        fields = [
            "id",
            "author",
            "tagged_users",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

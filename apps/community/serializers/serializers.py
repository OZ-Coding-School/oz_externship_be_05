from rest_framework import serializers

from apps.community.models.post_comment import PostComment
from apps.community.models.post_comment_tags import PostCommentTag


class PostCommentSerializer(serializers.ModelSerializer[PostComment]):

    class Meta:
        model = PostComment
        fields = [
            "content",
        ]
        read_only_fields = ["id", "author_id", "post_id", "created_at", "updated_at"]


class PostCommentTagsSerializer(serializers.ModelSerializer[PostCommentTag]):
    class Meta:
        model = PostCommentTag
        fields = [
            "tagged_user_id",
            "comment_id",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

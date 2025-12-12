from rest_framework import serializers

from apps.community.models.post_comment_tags import PostCommentTag


class PostCommentTagsSerializer(serializers.ModelSerializer[PostCommentTag]):
    class Meta:
        model = PostCommentTag
        fields = [
            "tagged_user",
            "comment",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

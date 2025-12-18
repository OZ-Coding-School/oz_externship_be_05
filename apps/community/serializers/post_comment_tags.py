from rest_framework import serializers

from apps.community.models.post_comment_tags import PostCommentTag


# apps/community/serializers/post_comment_tags.py
class PostCommentTagsSerializer(serializers.ModelSerializer[PostCommentTag]):
    class Meta:
        model = PostCommentTag
        fields = ["id", "tagged_user", "comment", "created_at", "updated_at"]
        read_only_fields = ["id", "comment", "created_at", "updated_at"]

from rest_framework import serializers
from .models.post_comment import PostComment
from .models.post_comment_tags import PostCommentTags

class PostCommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = PostComment
        fields = [
            "content",
        ]
        read_only_fields = [
            "id",
            "author_id",
            "post_id",
            "created_at",
            "updated_at"
        ]

class PostCommentTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostCommentTags
        fields = [
            "tagged_user_id",
            "comment_id",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at"
        ]


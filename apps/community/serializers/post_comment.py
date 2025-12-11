from rest_framework import serializers
from apps.community.models.post_comment import PostComment

class PostCommentSerializer(serializers.ModelSerializer[PostComment]):

    class Meta:
        model = PostComment
        fields = [
            "content",
        ]
        read_only_fields = ["id", "author_id", "post_id", "created_at", "updated_at"]
from rest_framework import serializers

from apps.community.models.post_comment import PostComment

#apps/community/serializers.py
class PostCommentSerializer(serializers.ModelSerializer[PostComment]):

    class Meta:
        model = PostComment
        fields = [
            "content",
        ]
        read_only_fields = ["id", "author", "post", "created_at", "updated_at"]

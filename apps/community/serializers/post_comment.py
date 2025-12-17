from typing import Any, Dict

from rest_framework import serializers

from apps.community.models.post_comment import PostComment
from apps.community.models.post_comment_tags import PostCommentTag
from apps.community.serializers.post_comment_tags import PostCommentTagsSerializer


# apps/community/serializers/post_comment.py
class PostCommentSerializer(serializers.ModelSerializer[PostComment]):
    tags = PostCommentTagsSerializer(many=True, required=False)

    class Meta:
        model = PostComment
        fields = [
            "tags",
            "content",
        ]
        read_only_fields = ["id", "author", "post", "created_at", "updated_at"]

    def create(self, validated_data: Dict[str, Any]) -> PostComment:
        tags_data = validated_data.pop("tags", [])
        comment = PostComment.objects.create(**validated_data)

        # 기존 시리얼라이저로 태그 생성
        for tag_data in tags_data:
            PostCommentTag.objects.create(comment=comment, tagged_user=tag_data["tagged_user"])

        return comment

    def update(self, comment: PostComment, validated_data: Dict[str, Any]) -> PostComment:
        tags_data = validated_data.pop("tags", None)

        for content, data in validated_data.items():
            setattr(comment, content, data)

        comment.save()

        if tags_data is not None:
            PostCommentTag.objects.filter(comment=comment).delete()

            for tag_data in tags_data:
                PostCommentTag.objects.create(comment=comment, tagged_user=tag_data["tagged_user"])

        else:
            pass

        return comment

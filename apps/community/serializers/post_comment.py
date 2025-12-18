from typing import Any, Dict

from rest_framework import serializers

from apps.community.models.post_comment import PostComment
from apps.community.models.post_comment_tags import PostCommentTag
from apps.community.serializers.post_comment_tags import PostCommentTagsSerializer


# apps/community/serializers/post_comment.py
class PostCommentSerializer(serializers.ModelSerializer[PostComment]):
    tagged_user = PostCommentTagsSerializer(many=True, required=False)

    class Meta:
        model = PostComment
        fields = [
            "id",
            "author",
            "tagged_user",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "post", "created_at", "updated_at"]

    def create(self, validated_data: Dict[str, Any]) -> PostComment:
        tags_data = validated_data.pop("tagged_user", [])
        comment = PostComment.objects.create(**validated_data)

        # set() = 중복을 허용하지 않는 자료형
        destroy_clone = set()
        for tag_data in tags_data:
            destroy_clone.add(tag_data["tagged_user"].id)

        # 중첩된 시리얼라이저로 태그 생성
        for tag_id in destroy_clone:
            PostCommentTag.objects.create(comment=comment, tagged_user_id=tag_id)

        return comment

    def update(self, comment: PostComment, validated_data: Dict[str, Any]) -> PostComment:
        tags_data = validated_data.pop("tagged_user", None)

        for content, data in validated_data.items():
            setattr(comment, content, data)

        comment.save()

        PostCommentTag.objects.filter(comment=comment).delete()

        if tags_data is not None:
            destroy_clone = set()
            for tag_data in tags_data:
                destroy_clone.add(tag_data["tagged_user"].id)

            for tag_id in destroy_clone:
                PostCommentTag.objects.create(comment=comment, tagged_user_id=tag_id)

        return comment

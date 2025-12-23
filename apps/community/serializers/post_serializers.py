from typing import Any, Dict, Optional

from rest_framework import serializers

from apps.community.models.post import Post
from apps.community.models.post_category import PostCategory
from apps.user.models import User


# 피드백 받은 공통검증 로직1 (카테고리 ID 검증 메서드 & 제목 검증 메서드)
class PostWriteFieldsSerializer(serializers.Serializer[Post]):
    title = serializers.CharField(required=True)
    content = serializers.CharField(required=True)
    category_id = serializers.IntegerField(required=True)

    def validate_category_id(self, value: int) -> int:
        if not PostCategory.objects.filter(id=value).exists():
            raise serializers.ValidationError("없는 카테고리입니다.")
        return value

    def validate_title(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("제목을 입력해주세요.")
        return value.strip()


# 피드백 받은 공통검증 로직2 (작성자 정보 가져오는 메서드 & 좋아요 개수를 가져오는 메서드)
class PostReadFieldsSerializerMixin(serializers.ModelSerializer[Post]):
    author = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()

    def get_author(self, obj: Post) -> Dict[str, Any]:
        author: User = obj.author
        return {
            "id": author.id,
            "name": author.nickname,
            "profile_image_url": getattr(author, "profile_image_url", None),
        }

    def get_like_count(self, obj: Post) -> int:
        return int(getattr(obj, "like_count", 0))


# 생성
class PostCreateSerializer(PostWriteFieldsSerializer):

    def create(self, validated_data: Dict[str, Any]) -> Post:
        user: User = self.context["request"].user

        return Post.objects.create(
            author=user,
            title=validated_data["title"],
            content=validated_data["content"],
            category_id=validated_data["category_id"],
        )

    def to_representation(self, instance: Post) -> Dict[str, Any]:
        return {
            "detail": "게시글이 성공적으로 등록되었습니다.",
            "post_id": instance.id,
        }


# 수정
class PostUpdateSerializer(PostWriteFieldsSerializer):

    def update(self, instance: Post, validated_data: Dict[str, Any]) -> Post:
        instance.title = validated_data["title"]
        instance.content = validated_data["content"]
        instance.category_id = validated_data["category_id"]
        instance.save()
        return instance

    def to_representation(self, instance: Post) -> Dict[str, Any]:
        return {
            "id": instance.id,
            "title": instance.title,
            "content": instance.content,
            "category_id": instance.category_id,
        }


# 조회
class PostListSerializer(PostReadFieldsSerializerMixin):
    thumbnail_img_url = serializers.SerializerMethodField()
    content_preview = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "title",
            "thumbnail_img_url",
            "content_preview",
            "comment_count",
            "view_count",
            "like_count",
            "created_at",
            "updated_at",
        ]

    def get_thumbnail_img_url(self, obj: Post) -> Optional[str]:
        return getattr(obj, "thumbnail_img_url", None)

    def get_content_preview(self, obj: Post) -> str:
        content: str = obj.content
        return content[:50] + "..." if len(content) > 50 else content

    def get_comment_count(self, obj: Post) -> int:
        return int(getattr(obj, "comment_count", 0))


# 상세조회
class PostDetailSerializer(PostReadFieldsSerializerMixin):
    category = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "category",
            "title",
            "content",
            "view_count",
            "like_count",
            "created_at",
            "updated_at",
        ]

    def get_category(self, obj: Post) -> Optional[Dict[str, Any]]:
        category = obj.category
        if obj.category is None:
            return None
        return {
            "id": category.id,
            "name": category.name,
        }

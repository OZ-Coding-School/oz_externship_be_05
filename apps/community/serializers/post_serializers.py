from typing import Any, Dict

from rest_framework import serializers

from apps.community.models.post import Post
from apps.community.models.post_category import PostCategory
from apps.user.models import User


# 생성
class PostCreateSerializer(serializers.Serializer[Post]):
    title = serializers.CharField(required=True)
    content = serializers.CharField(required=True)
    category_id = serializers.IntegerField(required=True)

    def validate_category_id(self, value: int) -> int:
        if not isinstance(value, int):
            raise serializers.ValidationError("카테고리 ID는 정수여야함.")
        return value

    def create(self, validated_data: Dict[str, Any]) -> Post:
        user: User = self.context["request"].user
        category_id = validated_data["category_id"]

        category = PostCategory.objects.get(id=category_id)

        return Post.objects.create(
            author=user,
            title=validated_data["title"],
            content=validated_data["content"],
            category_id=validated_data["category_id"],
        )

    def to_representation(self, instance: Post) -> Dict[str, Any]:
        return {
            "detail": "게시글이 성공적 등록됨.",
            "post_id": instance.id,
        }


# 수정
class PostUpdateSerializer(serializers.Serializer[Post]):
    title = serializers.CharField(required=True, max_length=50)
    content = serializers.CharField(required=True)
    category_id = serializers.IntegerField(required=True)

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
class PostListSerializer(serializers.ModelSerializer[Post]):
    author = serializers.SerializerMethodField()
    thumbnail_img_url = serializers.SerializerMethodField()
    content_preview = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()

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

    def get_author(self, obj: Post) -> Dict[str, Any]:
        author: User = obj.author
        return {
            "id": author.id,
            "nickname": author.nickname,
            "profile_img_url": getattr(author, "profile_img_url", None),
        }

    def get_thumbnail_img_url(self, obj: Post) -> Any:
        return getattr(obj, "thumbnail_img_url", None)

    def get_content_preview(self, obj: Post) -> str:
        content: str = obj.content
        return content[:50] + "..." if len(content) > 50 else content

    def get_comment_count(self, obj: Post) -> int:
        return int(getattr(obj, "comment_count", 0))

    def get_like_count(self, obj: Post) -> int:
        return int(getattr(obj, "like_count", 0))


# 상세조회
class PostDetailSerializer(serializers.ModelSerializer[Post]):
    author = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()

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

    def get_author(self, obj: Post) -> Dict[str, Any]:
        author: User = obj.author
        return {
            "id": obj.author.id,
            "nickname": obj.author.nickname,
            "profile_img_url": getattr(author, "profile_img_url", None),
        }

    def get_category(self, obj: Post) -> Dict[str, Any]:
        category = obj.category
        if obj.category is None:
            return None
        return {
            "id": obj.category.id,
            "name": category.name,
        }

    def get_like_count(self, obj: Post) -> int:
        return int(getattr(obj, "like_count", 0))

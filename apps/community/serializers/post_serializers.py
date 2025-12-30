from rest_framework import serializers

from apps.community.models.post import Post
from apps.community.models.post_category import PostCategory
from apps.user.models import User


# 피드백 받은 공통검증 로직1 (카테고리 ID 검증 메서드 & 제목 검증 메서드)
class PostCreateUpdateSerializer(serializers.ModelSerializer[Post]):
    class Meta:
        model = Post
        fields = ["id", "title", "content", "category"]


class PostAuthorSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["id", "nickname", "profile_image_url"]
        read_only_fields = fields


class PostCategorySerializer(serializers.ModelSerializer[PostCategory]):
    class Meta:
        model = PostCategory
        fields = ["id", "name"]
        read_only_fields = fields


# 피드백 받은 공통검증 로직2 (작성자 정보 가져오는 메서드 & 좋아요 개수를 가져오는 메서드)
class PostReadSerializer(serializers.ModelSerializer[Post]):
    author = PostAuthorSerializer(read_only=True)
    like_count = serializers.IntegerField(default=0, read_only=True)
    comment_count = serializers.IntegerField(default=0, read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "author",
            "content",
            "like_count",
            "comment_count",
            "view_count",
            "created_at",
            "updated_at",
        ]


# 조회
class PostListSerializer(PostReadSerializer):
    thumbnail_img_url = serializers.CharField(source="post_images.first", read_only=True)
    content_preview = serializers.CharField(read_only=True)

    class Meta(PostReadSerializer.Meta):
        fields = PostReadSerializer.Meta.fields + ["thumbnail_img_url", "content_preview"]


# 상세조회
class PostDetailSerializer(PostReadSerializer):
    category = PostCategorySerializer(read_only=True)

    class Meta(PostReadSerializer.Meta):
        fields = PostReadSerializer.Meta.fields + ["category"]

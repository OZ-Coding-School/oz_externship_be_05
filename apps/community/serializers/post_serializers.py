from rest_framework import serializers
from apps.community.models.post import Post

class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "author_id",
            "author_username",
            "category",
            "category_name",
            "title",
            "content",
            "view_count",
            "is_visible",
            "is_notice",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id","created_at","updated_at","author_id","view_count"]

    #전체 데이터 유효성 검사 코드
    def validate(self, attrs):
        # 공지글 규칙 코드
        if attrs.get("is_notice") and len(attrs.get("content","")) < 20:
            raise serializers.ValidationError("공지글은 20글자 이상으로 적어주세요.")

        # 일반 게시글 규칙 코드
        if not attrs.get("is_notice") and len(attrs.get("content","")) < 10:
            raise serializers.ValidationError("게시글은 10글자 이상으로 적어주세요.")
        return attrs

    # 게시물을 만들때 작성자 자동 설정
    def create(self, validated_data):
        user = self.context["request"].user
        return Post.objects.create(author=user, **validated_data)

    #게시물을 업데이트 할 때 조회수 보호
    def update(self,instance,validated_data):
        validated_data.pop("view_count",None)
        for attr, value in validated_data.items():
            setattr(instance,attr,value)
        instance.save()
        return instance
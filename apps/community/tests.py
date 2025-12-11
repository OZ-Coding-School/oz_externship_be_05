from datetime import date
from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from apps.community.models.post import Post
from apps.community.models.post_category import PostCategory
from apps.community.serializers.post_serializers import PostSerializer

User = get_user_model()


class PostModelTest(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

        self.user = User.objects.create_user(
            password="1234",
            email="test@test.com",
            name="테스터",
            birthday=date(2000, 11, 21),
        )
        self.category = PostCategory.objects.create(name="공지")

        self.request = self.factory.post("/fake-url/")
        self.request.user = self.user

    def get_serializer(self, data: Optional[Dict[str, Any]] = None, instance: Optional[Post] = None) -> PostSerializer:
        return PostSerializer(data=data, instance=instance, context={"request": self.request}, partial=True)

    def test_create_normal_post(self) -> None:
        data = {
            "category": self.category.id,
            "title": "공지글",
            "content": "공지글은 2글자 이상으로 등록해야 정상적으로 통과됩니다.!",
            "is_notice": True,
            "is_visible": True,
        }
        serializer = self.get_serializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_notice_post_validation_fail(self) -> None:
        data = {
            "category": self.category.id,
            "title": "공지",
            "content": "짧",
            "is_notice": True,
        }
        serializer = self.get_serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("공지글은 2글자 이상으로 적어주세요.", str(serializer.errors))

    def test_update_post_protect_view_count(self) -> None:
        post = Post.objects.create(
            author=self.user, category=self.category, title="원본", content="원본 내용!", view_count=50
        )

        update_data = {
            "title": "수정됨.",
            "content": "수정된 내용!",
            "view_count": 9999,
        }

        serializer = PostSerializer(data=update_data, instance=post, context={"request": self.request}, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_post = serializer.save()

        self.assertEqual(updated_post.title, "수정됨.")
        self.assertEqual(updated_post.view_count, 50)

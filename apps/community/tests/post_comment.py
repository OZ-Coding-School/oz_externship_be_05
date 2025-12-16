from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, force_authenticate
from datetime import datetime
from apps.community.models.post import Post
from apps.community.models.post_comment import PostComment
from apps.community.models.post_category import PostCategory

User = get_user_model()

class TestPostCommentListCreateAPIView(TestCase):

    def setUp(self):
        self.client = APIClient()


        test_user = User.objects.create_user(
            name="testuser",
            password="password",
            email="test@test.com",
            birthday=datetime.now()

        )

        category = PostCategory.objects.create(name="테스트")

        self.post = Post.objects.create(
            title="제목",
            content="내용",
            author=test_user,
            category=category
        )

        PostComment.objects.create(
            post=self.post,
            author=test_user,
            content="댓글1"
        )
        PostComment.objects.create(
            post=self.post,
            author=test_user,
            content="댓글2"
        )

        self.url = f"/api/v1/posts/{self.post.id}/comments"

    def test_get_comments(self):
        user = User.objects.first()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


    def test_create_comment_success(self):
        user = User.objects.first()
        self.client.force_authenticate(user=user)

        data = {"content": "새 댓글"}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['detail'], "댓글이 등록되었습니다.")
        self.assertEqual(PostComment.objects.filter(post=self.post).count(), 3)



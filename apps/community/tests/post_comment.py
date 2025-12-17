from datetime import datetime

from django.test import TestCase
from rest_framework.test import APITestCase

from apps.community.models.post import Post
from apps.community.models.post_category import PostCategory
from apps.community.models.post_comment import PostComment
from apps.user.models import User


class TestPostCommentListCreateAPIView(APITestCase):

    def setUp(self):

        test_user = User.objects.create_user(
            name="test_user", password="password", email="test@test.com", birthday=datetime.now()
        )

        tagged_user = User.objects.create_user(
            name="tag_user",
            password="password123",
            email="tag@tag.com",
            birthday=datetime.now()
        )

        category = PostCategory.objects.create(name="테스트")

        self.post = Post.objects.create(title="제목", content="내용", author=test_user, category=category)

        PostComment.objects.create(post=self.post, author=test_user, content="댓글1")
        PostComment.objects.create(post=self.post, author=test_user, content="댓글2")

        self.post_url = f"/api/v1/posts/{self.post.id}/comments"

    def test_get_comments(self):
        user = User.objects.first()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.post_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_get_comments_not_exist(self):
        user = User.objects.first()
        self.client.force_authenticate(user=user)

        response = self.client.get(f"/api/v1/posts/999/comments")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "해당 게시글을 찾을 수 없습니다.")

    def test_create_comment(self):
        user = User.objects.first()
        self.client.force_authenticate(user=user)

        data = {"content": "새 댓글"}
        response = self.client.post(self.post_url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["detail"], "댓글이 등록되었습니다.")
        self.assertEqual(PostComment.objects.filter(post=self.post).count(), 3)

    def test_create_comment_with_empty_content(self):
        user = User.objects.first()
        self.client.force_authenticate(user=user)

        data = {"content": ""}
        response = self.client.post(self.post_url, data)

        self.assertEqual(response.status_code, 400)

    def test_create_comment_with_tagged_user(self):
        user = User.objects.first()
        self.client.force_authenticate(user=user)

        data = {"content": "새 댓글",
                "tagged_user": user.id}

        response = self.client.post(self.post_url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["detail"], "댓글이 등록되었습니다.")


class TestPostCommentUpdateDestroyAPIView(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            name="test_user", password="password", email="test@test.com", birthday=datetime.now()
        )

        self.other_user = User.objects.create_user(
            name="other_user", password="password", email="other@test.com", birthday=datetime.now()
        )

        tagged_user = User.objects.create_user(
            name="tag_user",
            password="password123",
            email="tag@tag.com",
            birthday=datetime.now()
        )

        category = PostCategory.objects.create(name="테스트")

        self.post = Post.objects.create(title="제목", content="내용", author=self.user, category=category)

        self.comment = PostComment.objects.create(post=self.post, author=self.user, content="댓글")

        self.comment_url = f"/api/v1/posts/{self.post.id}/comments/{self.comment.id}"

    def test_update_comment(self):
        self.client.force_authenticate(user=self.user)

        data = {"content": "수정 댓글"}
        response = self.client.put(self.comment_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["content"], "수정 댓글")

    def test_update_comment_by_other(self):
        self.client.force_authenticate(user=self.other_user)

        data = {"content": "수정 댓글"}
        response = self.client.put(self.comment_url, data)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["detail"], "권한이 없습니다.")

    def test_update_comment_not_exist(self):
        self.client.force_authenticate(user=self.user)

        data = {"content": "수정 시도"}
        response = self.client.put(f"/api/v1/posts/{self.post.id}/comments/999", data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "해당 댓글을 찾을 수 없습니다.")

    def test_update_comment_with_empty_content(self):
        self.client.force_authenticate(user=self.user)

        data = {"content": ""}
        response = self.client.put(self.comment_url, data)

        self.assertEqual(response.status_code, 400)

    def test_update_comment_with_tagged_user(self):
        self.client.force_authenticate(user=self.user)

        data = {"content": "태그 수정",
                "tagged_user": self.user.id}
        response = self.client.put(self.comment_url, data)

        self.assertEqual(response.status_code, 200)

    def test_delete_comment_not_exist(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(f"/api/v1/posts/{self.post.id}/comments/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "해당 댓글을 찾을 수 없습니다.")

    def test_delete_comment_by_other(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(self.comment_url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["detail"], "권한이 없습니다.")

    def test_delete_comment(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(self.comment_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["detail"], "댓글이 삭제되었습니다.")

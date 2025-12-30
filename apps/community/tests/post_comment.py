from datetime import datetime
from typing import Any, Dict

from rest_framework.test import APITestCase

from apps.community.models.post import Post
from apps.community.models.post_category import PostCategory
from apps.community.models.post_comment import PostComment
from apps.community.models.post_comment_tags import PostCommentTag
from apps.user.models import User


class APITestCaseBase(APITestCase):

    def check_response(self, response_data: Dict[str, Any], author_id: int, content: str) -> None:
        self.assertIn("id", response_data)
        self.assertIn("content", response_data)
        self.assertIn("author", response_data)

        self.assertEqual(response_data["author"]["id"], author_id)
        self.assertEqual(response_data["content"], content)


class TestPostCommentListCreateAPIView(APITestCaseBase):

    def setUp(self) -> None:

        self.test_user = User.objects.create_user(
            name="test_user", password="password", email="test@test.com", birthday=datetime.now()
        )

        self.other_user = User.objects.create_user(
            name="other_user", password="password", nickname="누구", email="other@other.com", birthday=datetime.now()
        )

        self.tagged_user = User.objects.create_user(
            name="tagged_user", password="password", nickname="태그", email="tagged@tagged.com", birthday=datetime.now()
        )

        category = PostCategory.objects.create(name="테스트")

        self.post = Post.objects.create(title="제목", content="내용", author=self.test_user, category=category)

        self.comment1 = PostComment.objects.create(post=self.post, author=self.test_user, content="댓글1")
        self.comment2 = PostComment.objects.create(post=self.post, author=self.test_user, content="댓글2")
        self.comment3 = PostComment.objects.create(post=self.post, author=self.other_user, content="댓글3")

        PostCommentTag.objects.create(comment=self.comment1, tagged_user=self.tagged_user)
        PostCommentTag.objects.create(comment=self.comment1, tagged_user=self.other_user)
        PostCommentTag.objects.create(comment=self.comment2, tagged_user=self.tagged_user)

        self.post_url = f"/api/v1/posts/{self.post.id}/comments"

        self.client.force_authenticate(user=self.test_user)

    def test_get_comments(self) -> None:

        response = self.client.get(self.post_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)

        check_author_id = [1, 1, 2]
        check_content = ["댓글1", "댓글2", "댓글3"]

        for i, comment in enumerate(response.data["results"]):

            self.check_response(comment, check_author_id[i], check_content[i])

    def test_get_comments_not_exist(self) -> None:

        response = self.client.get(f"/api/v1/posts/999/comments")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error_detail"], "게시글을(를) 찾을 수 없습니다.")

    def test_create_comment_without_tag(self) -> None:

        data = {"content": "태그 없는 댓글"}
        response = self.client.post(self.post_url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["detail"], "댓글이 등록되었습니다.")

    def test_create_comment_with_tags(self) -> None:

        data = {"content": "@태그 @누구 태그 있는 댓글"}
        response = self.client.post(self.post_url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["detail"], "댓글이 등록되었습니다.")

        comment = PostComment.objects.get(content="@태그 @누구 태그 있는 댓글")
        self.assertIsNotNone(comment)
        self.assertEqual(comment.author, self.test_user)

        tags = PostCommentTag.objects.filter(comment=comment)
        check_author_id = [self.other_user.id, self.tagged_user.id]
        tui = []
        for tag in tags:
            tui.append(tag.tagged_user.id)

        self.assertEqual(check_author_id, tui)

    def test_create_comment_with_tag(self) -> None:

        data = {"content": "@태그 @태그 태그 있는 댓글"}
        response = self.client.post(self.post_url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["detail"], "댓글이 등록되었습니다.")

        comment = PostComment.objects.get(content="@태그 @태그 태그 있는 댓글")
        self.assertIsNotNone(comment)
        self.assertEqual(comment.author, self.test_user)

        tags = PostCommentTag.objects.filter(comment=comment)

        for tag in tags:
            self.assertEqual(self.tagged_user.id, tag.tagged_user.id)

    def test_create_comment_with_empty_content(self) -> None:

        data = {"content": ""}
        response = self.client.post(self.post_url, data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["errors"]["content"][0], "이 필드는 필수 항목입니다.")

    def test_create_comment_without_auth(self) -> None:
        self.client.force_authenticate(user=None)

        data = {"content": "댓글"}
        response = self.client.post(self.post_url, data)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.data["error_detail"], "자격 인증데이터(authentication credentials)가 제공되지 않았습니다."
        )

    def test_create_comment_without_not_exist(self) -> None:
        data = {"content": "댓글"}
        response = self.client.post(f"/api/v1/posts/999/comments", data)

        print(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error_detail"], "게시글을(를) 찾을 수 없습니다.")


class TestPostCommentUpdateDestroyAPIView(APITestCaseBase):
    def setUp(self) -> None:

        self.test_user = User.objects.create_user(
            name="test_user", password="password", email="test@test.com", birthday=datetime.now()
        )

        self.other_user = User.objects.create_user(
            name="other_user", password="password", nickname="누구", email="other@other.com", birthday=datetime.now()
        )

        self.tagged_user = User.objects.create_user(
            name="tagged_user", password="password", nickname="태그", email="tagged@tagged.com", birthday=datetime.now()
        )

        category = PostCategory.objects.create(name="테스트")

        self.post = Post.objects.create(title="제목", content="내용", author=self.test_user, category=category)

        self.comment = PostComment.objects.create(post=self.post, author=self.test_user, content="댓글1")

        PostCommentTag.objects.create(comment=self.comment, tagged_user=self.tagged_user)

        self.post_url = f"/api/v1/posts/{self.post.id}/comments"
        self.comment_url = f"/api/v1/posts/{self.post.id}/comments/{self.comment.id}"

        self.client.force_authenticate(user=self.test_user)

    def test_update_comment_without_tag(self) -> None:
        data = {"content": "댓글 수정"}
        response = self.client.put(self.comment_url, data, format="json")

        comment = PostComment.objects.get(content="댓글 수정")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.comment.id)
        self.assertEqual(response.data["content"], "댓글 수정")
        self.assertIn("updated_at", response.data)

        self.assertFalse(PostCommentTag.objects.filter(comment=comment).exists())

    def test_update_comment_with_tag(self) -> None:
        data = {"content": "@태그 댓글 수정"}
        response = self.client.put(self.comment_url, data, format="json")

        comment = PostComment.objects.get(content="@태그 댓글 수정")

        print(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.comment.id)
        self.assertEqual(response.data["content"], "@태그 댓글 수정")
        self.assertIn("updated_at", response.data)

        self.assertTrue(PostCommentTag.objects.filter(comment=comment).exists())
        self.assertEqual(PostCommentTag.objects.filter(comment=comment).count(), 1)

    def test_update_comment_with_tags(self) -> None:
        data = {"content": "@태그 @누구 댓글 수정"}
        response = self.client.put(self.comment_url, data, format="json")

        comment = PostComment.objects.get(content="@태그 @누구 댓글 수정")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.comment.id)
        self.assertEqual(response.data["content"], "@태그 @누구 댓글 수정")
        self.assertIn("updated_at", response.data)

        self.assertTrue(PostCommentTag.objects.filter(comment=comment).exists())
        self.assertEqual(PostCommentTag.objects.filter(comment=comment).count(), 2)

    def test_update_comment_by_other_user(self) -> None:
        self.client.force_authenticate(user=self.other_user)

        data = {"content": "댓글 수정"}
        response = self.client.put(self.comment_url, data)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error_detail"], "권한이 없습니다.")

    def test_update_comment_not_exist(self) -> None:
        data = {"content": "댓글 수정"}
        response = self.client.put(f"/api/v1/posts/{self.post.id}/comments/999", data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error_detail"], "해당 댓글을 찾을 수 없습니다.")

    def test_update_comment_with_empty_content(self) -> None:
        data = {"content": ""}
        response = self.client.put(self.comment_url, data)

        print(response.data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["errors"]["content"][0], "이 필드는 필수 항목입니다.")

    def test_update_comment_without_auth(self) -> None:
        self.client.force_authenticate(user=None)

        data = {"content": "댓글 수정"}
        response = self.client.put(self.post_url, data)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.data["error_detail"], "자격 인증데이터(authentication credentials)가 제공되지 않았습니다."
        )

    def test_delete_comment_not_exist(self) -> None:
        response = self.client.delete(f"/api/v1/posts/{self.post.id}/comments/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error_detail"], "해당 댓글을 찾을 수 없습니다.")

    def test_delete_comment_by_other(self) -> None:
        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(self.comment_url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error_detail"], "권한이 없습니다.")

    def test_delete_comment_without_auth(self) -> None:
        self.client.force_authenticate(user=None)

        response = self.client.delete(self.comment_url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.data["error_detail"], "자격 인증데이터(authentication credentials)가 제공되지 않았습니다."
        )

    def test_delete_comment(self) -> None:
        response = self.client.delete(self.comment_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["detail"], "댓글이 삭제되었습니다.")

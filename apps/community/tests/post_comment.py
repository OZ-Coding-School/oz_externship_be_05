from datetime import datetime

from django.test import TestCase
from django.db.models import QuerySet
from rest_framework.test import APITestCase

from apps.community.models import PostCommentTag
from apps.community.models.post import Post
from apps.community.models.post_category import PostCategory
from apps.community.models.post_comment import PostComment
from apps.user.models import User


class TestPostCommentListCreateAPIView(APITestCase):

    def setUp(self) -> None:

        self.test_user = User.objects.create_user(
            name="test_user", password="password", email="test@test.com", birthday=datetime.now()
        )

        self.other_user = User.objects.create_user(
            name="other_user", password="password", email="other@other.com", birthday=datetime.now()
        )

        self.tagged_user = User.objects.create_user(
            name="tagged_user", password="password", email="tagged@tagged.com", birthday=datetime.now()
        )

        category = PostCategory.objects.create(name="테스트")

        self.post = Post.objects.create(title="제목", content="내용", author=self.test_user, category=category)

        PostComment.objects.create(post=self.post, author=self.test_user, content="댓글1")
        PostComment.objects.create(post=self.post, author=self.test_user, content="댓글2")

        self.post_url = f"/api/v1/posts/{self.post.id}/comments"

        self.client.force_authenticate(user=self.test_user)

    def check_response(self, response_data, author_name, content):
        self.assertIn('id', response_data)
        self.assertIn('content', response_data)
        self.assertIn('author', response_data)

        self.assertEqual(User.objects.get(id=response_data['author']).name, author_name)
        self.assertEqual(response_data['content'], content)

    def test_get_comments(self) -> None:

        response = self.client.get(self.post_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        check_content = ['댓글1', '댓글2']

        for i, comment in enumerate(response.data):

            self.check_response(comment,"test_user",check_content[i])


    def test_get_comments_not_exist(self) -> None:

        response = self.client.get(f"/api/v1/posts/999/comments")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error_detail"], "해당 게시글을 찾을 수 없습니다.")

    def test_create_comment(self) -> None:

        data = {"content": "새 댓글"}
        response = self.client.post(self.post_url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(PostComment.objects.filter(post=self.post).count(), 3)

        self.check_response(response.data,"test_user","새 댓글")


    def test_create_comment_with_empty_content(self) -> None:

        data = {"content": ""}
        response = self.client.post(self.post_url, data)

        self.assertEqual(response.status_code, 400)

    def test_create_comment_with_tagged_user(self) -> None:

        data = {"content": "새 댓글", "tagged_user": [{"tagged_user": self.tagged_user.id}]}

        response = self.client.post(self.post_url, data, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(PostComment.objects.filter(post=self.post).count(), 3)

        self.check_response(response.data,"test_user","새 댓글")

        comment = PostComment.objects.filter(post=self.post).latest('id')
        comment_tag = PostCommentTag.objects.get(comment_id=comment.id)

        self.assertIsNotNone(comment_tag)
        self.assertEqual(comment_tag.tagged_user.id, self.tagged_user.id)
        self.assertEqual(User.objects.get(id=comment_tag.tagged_user.id).name, "tagged_user")

    def test_create_comment_with_tagged_users(self) -> None:

        data = {"content": "새 댓글", "tagged_user": [{"tagged_user": self.other_user.id},{"tagged_user": self.tagged_user.id}]}

        response = self.client.post(self.post_url, data, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(PostComment.objects.filter(post=self.post).count(), 3)

        self.check_response(response.data,"test_user","새 댓글")

        comment = PostComment.objects.filter(post=self.post).latest('id')
        comment_tags = PostCommentTag.objects.filter(comment_id=comment.id)

        self.assertIsNotNone(comment_tags)

        check_users = [self.other_user.id,self.tagged_user.id ]
        check_names = ["other_user","tagged_user" ]

        for i, comment_tag in enumerate(comment_tags):

            self.assertEqual(comment_tag.tagged_user.id, check_users[i])
            self.assertEqual(User.objects.get(id=comment_tag.tagged_user.id).name, check_names[i])


class TestPostCommentUpdateDestroyAPIView(APITestCase):

    def setUp(self) -> None:
        self.test_user = User.objects.create_user(
            name="test_user", password="password", email="test@test.com", birthday=datetime.now()
        )

        self.other_user = User.objects.create_user(
            name="other_user", password="password", email="other@test.com", birthday=datetime.now()
        )

        self.tagged_user = User.objects.create_user(
            name="tagged_user", password="password", email="tagged@tagged.com", birthday=datetime.now()
        )

        category = PostCategory.objects.create(name="테스트")

        self.post = Post.objects.create(title="제목", content="내용", author=self.test_user, category=category)

        self.comment = PostComment.objects.create(post=self.post, author=self.test_user, content="댓글")

        self.comment_tag = PostCommentTag.objects.create(comment=self.comment, tagged_user=self.tagged_user)

        self.comment_url = f"/api/v1/posts/{self.post.id}/comments/{self.comment.id}"

        self.client.force_authenticate(user=self.test_user)

    def check_response(self, response_data, author_name, content):
            self.assertIn('id', response_data)
            self.assertIn('content', response_data)
            self.assertIn('author', response_data)

            self.assertEqual(User.objects.get(id=response_data['author']).name, author_name)
            self.assertEqual(response_data['content'], content)

    def test_update_comment(self) -> None:
        data = {"content": "수정 댓글", "tagged_user": [{"tagged_user": self.tagged_user.id}]}
        response = self.client.put(self.comment_url, data,format='json')

        self.assertEqual(response.status_code, 200)

        self.check_response(response.data,"test_user","수정 댓글")

        comment = PostComment.objects.filter(post=self.post).latest('id')
        comment_tag = PostCommentTag.objects.get(comment_id=comment.id)

        self.assertIsNotNone(comment_tag)
        self.assertEqual(comment_tag.tagged_user.id, self.tagged_user.id)
        self.assertEqual(User.objects.get(id=comment_tag.tagged_user.id).name, "tagged_user")



    def test_update_comment_by_other(self) -> None:
        self.client.force_authenticate(user=self.other_user)

        data = {"content": "수정 댓글"}
        response = self.client.put(self.comment_url, data)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error_detail"], "권한이 없습니다.")

    def test_update_comment_not_exist(self) -> None:
        data = {"content": "수정 시도"}
        response = self.client.put(f"/api/v1/posts/{self.post.id}/comments/999", data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error_detail"], "해당 댓글을 찾을 수 없습니다.")

    def test_update_comment_with_empty_content(self) -> None:
        data = {"content": ""}
        response = self.client.put(self.comment_url, data)

        self.assertEqual(response.status_code, 400)

    def test_update_comment_with_add_tag(self) -> None:
        data = {"content": "태그 추가", "tagged_user": [{"tagged_user": self.tagged_user.id},{"tagged_user": self.other_user.id}]}
        response = self.client.put(self.comment_url, data)

        self.assertEqual(response.status_code, 200)

        comment = PostComment.objects.filter(post=self.post).latest('id')
        comment_tags = PostCommentTag.objects.filter(comment_id=comment.id)

        check_users = [self.other_user.id,self.tagged_user.id ]
        check_names = ["other_user","tagged_user" ]

        for i, comment_tag in enumerate(comment_tags):

            self.assertEqual(comment_tag.tagged_user.id, check_users[i])
            self.assertEqual(User.objects.get(id=comment_tag.tagged_user.id).name, check_names[i])



    def test_update_comment_change_tag(self)-> None:
        data = {"content": "태그 변경", "tagged_user": [{"tagged_user": self.other_user.id}]}
        response = self.client.put(self.comment_url, data,format='json')

        self.assertEqual(response.status_code, 200)

        comment = PostComment.objects.filter(post=self.post).latest('id')
        comment_tag = PostCommentTag.objects.get(comment_id=comment.id)

        self.assertIsNotNone(comment_tag)
        self.assertEqual(comment_tag.tagged_user.id, self.other_user.id)
        self.assertEqual(User.objects.get(id=comment_tag.tagged_user.id).name, "other_user")



    def test_update_comment_delete_tag(self)-> None:
        data = {"content": "태그 제거"}
        response = self.client.put(self.comment_url, data)

        self.assertEqual(response.status_code, 200)

        comment = PostComment.objects.filter(post=self.post).latest('id')
        self.assertFalse(PostCommentTag.objects.filter(comment_id=comment.id).exists())

    def test_delete_comment_not_exist(self) -> None:
        response = self.client.delete(f"/api/v1/posts/{self.post.id}/comments/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error_detail"], "해당 댓글을 찾을 수 없습니다.")

    def test_delete_comment_by_other(self) -> None:
        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(self.comment_url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error_detail"], "권한이 없습니다.")

    def test_delete_comment(self) -> None:
        response = self.client.delete(self.comment_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["detail"], "댓글이 삭제되었습니다.")

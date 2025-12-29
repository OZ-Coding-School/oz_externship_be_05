from django.contrib.admin import AdminSite
from django.http import QueryDict

from apps.community.admin.post_admin import PostAdmin
from apps.community.admin.utils.filter import (
    CustomSearchFilter,
    PostOrderingFilter,
)
from apps.community.models.post import Post
from apps.community.tests.test_base import BasePostTestCase


class PostAdminTest(BasePostTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.site = AdminSite()
        self.admin = PostAdmin(Post, self.site)

    def test_likes_count(self) -> None:
        request = self.factory.get("/")
        qs = self.admin.get_queryset(request)
        obj = qs.get(id=self.post1.id)
        likes_count = self.admin.likes_count(obj)
        self.assertEqual(likes_count, 1)

    def test_comments_count(self) -> None:
        request = self.factory.get("/")
        qs = self.admin.get_queryset(request)
        obj = qs.get(id=self.post1.id)
        comment_count = self.admin.comment_count(obj)
        self.assertEqual(comment_count, 1)

    def test_PostOrderingFilter_newest(self) -> None:
        request = self.factory.get("/", query_params={"post_order_by": "newest"})
        params = QueryDict(mutable=True)
        params.setlist("post_order_by", ["newest"])
        filter_inst = PostOrderingFilter(request, params, Post, self.admin)

        qs = self.admin.get_queryset(request)
        filtered_qs = filter_inst.queryset(request, qs)

        self.assertEqual(filtered_qs.first(), self.post2)

    def test_PostOrderingFilter_oldest(self) -> None:
        request = self.factory.get("/", query_params={"post_order_by": "oldest"})
        params = QueryDict(mutable=True)
        params.setlist("post_order_by", ["oldest"])
        filter_inst = PostOrderingFilter(request, params, Post, self.admin)

        qs = self.admin.get_queryset(request)
        filtered_qs = filter_inst.queryset(request, qs)

        self.assertEqual(filtered_qs.first(), self.post1)

    def test_PostOrderingFilter_most_views(self) -> None:
        request = self.factory.get("/", query_params={"post_order_by": "most_views"})
        params = QueryDict(mutable=True)
        params.setlist("post_order_by", ["most_views"])
        filter_inst = PostOrderingFilter(request, params, Post, self.admin)
        qs = self.admin.get_queryset(request)
        filtered_qs = filter_inst.queryset(request, qs)

        self.assertEqual(filtered_qs.first(), self.post2)

    def test_PostOrderingFilter_most_likes(self) -> None:
        request = self.factory.get("/", query_params={"post_order_by": "most_likes"})
        params = QueryDict(mutable=True)
        params.setlist("post_order_by", ["most_likes"])
        filter_inst = PostOrderingFilter(request, params, Post, self.admin)
        qs = self.admin.get_queryset(request)
        filtered_qs = filter_inst.queryset(request, qs)

        self.assertEqual(filtered_qs.first(), self.post1)

    def test_CustomSearchFilter_author(self) -> None:
        params_dict = {"search_target": "title", "q": "test"}
        request = self.factory.get("/", data=params_dict)
        params = QueryDict(mutable=True)
        params.update(params_dict)
        filter_inst = CustomSearchFilter(request, params, Post, self.admin)
        qs = self.admin.get_queryset(request)
        filtered_qs = filter_inst.queryset(request, qs)

        self.assertEqual(filtered_qs.count(), 2)

    def test_CustomSearchFilter_title(self) -> None:
        params_dict = {"search_target": "title", "q": "1"}
        request = self.factory.get("/", data=params_dict)
        params = QueryDict(mutable=True)
        params.update(params_dict)

        filter_inst = CustomSearchFilter(request, params, Post, self.admin)
        qs = self.admin.get_queryset(request)
        filtered_qs = filter_inst.queryset(request, qs)

        self.assertEqual(filtered_qs.count(), 1)

    def test_CustomSearchFilter_content(self) -> None:
        params_dict = {"search_target": "content", "q": "2"}
        request = self.factory.get("/", data=params_dict)
        params = QueryDict(mutable=True)
        params.update(params_dict)

        filter_inst = CustomSearchFilter(request, params, Post, self.admin)
        qs = self.admin.get_queryset(request)
        filtered_qs = filter_inst.queryset(request, qs)

        self.assertEqual(filtered_qs.count(), 1)
        self.assertEqual(filtered_qs.first().title, "testpost2")

    def test_CustomSearchFilter_title_content(self) -> None:
        params_dict = {"search_target": "title_content", "q": "2"}
        request = self.factory.get("/", data=params_dict)
        params = QueryDict(mutable=True)
        params.update(params_dict)

        filter_inst = CustomSearchFilter(request, params, Post, self.admin)
        qs = self.admin.get_queryset(request)
        filtered_qs = filter_inst.queryset(request, qs)

        self.assertEqual(filtered_qs.count(), 1)
        self.assertEqual(filtered_qs.first().title, "testpost2")

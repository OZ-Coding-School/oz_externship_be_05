from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.community.models.post import Post
from apps.community.models.post_category import PostCategory
from apps.community.models.post_comment import PostComment
from apps.community.models.post_images import PostImage
from apps.community.models.post_likes import PostLike


class BasePostTestCase(APITestCase):
    """
    관리자 만들기 귀찮아서 만들엇습니다 상속받아서 쓰세요!
    """

    def setUp(self) -> None:
        # 1. 관리자 생성 및 강제 인증
        self.admin_user = get_user_model().objects.create_superuser(
            id=1,
            name="testuser",
            email="test@test.com",
            password="qwer1234!",
            birthday=date(2007, 8, 31),
        )
        self.client.force_authenticate(user=self.admin_user)

        self.factory = RequestFactory()

        self.post1 = Post.objects.create(
            id=1,
            title="testpost1",
            content="testcontent1",
            view_count=1,
            author_id=1,
            category_id=1,
            created_at=timezone.now(),
        )

        self.post2 = Post.objects.create(
            id=2,
            title="testpost2",
            content="testcontent2",
            view_count=2,
            author_id=1,
            category_id=1,
            created_at=timezone.now() - timedelta(days=1),
        )

        self.category = PostCategory.objects.create(
            id=1,
            name="testcategory",
            status=True,
        )
        self.comment = PostComment.objects.create(
            id=1,
            content="testcomment",
            author_id=1,
            post_id=1,
        )
        self.like = PostLike.objects.create(
            id=1,
            is_liked=True,
            post_id=1,
            user_id=1,
        )
        self.image = PostImage.objects.create(
            id=1,
            img_url="http://testimage.com/test.jpg",
            post_id=1,
        )

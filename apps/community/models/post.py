from django.db import models

from apps.community.models.post_category import PostCategory
from apps.core.models import TimeStampedModel
from apps.user.models import User


class Post(TimeStampedModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(PostCategory, on_delete=models.CASCADE, related_name="post")
    title = models.CharField(max_length=50)
    content = models.TextField()
    view_count = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    is_notice = models.BooleanField(default=False)

    class Meta:
        db_table = "post"

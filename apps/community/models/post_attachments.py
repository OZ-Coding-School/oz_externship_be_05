from django.db import models

from apps.community.models.post import Post


class PostAttachment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    file_url = models.URLField()
    file_name = models.CharField(max_length=50)

    class Meta:
        db_table = "post_attachments"

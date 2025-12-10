from django.db import models
from apps.user.models import User
from apps.post_comment.models import PostComment

class PostCommentTags(models.Model):
    tagged_user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "post_comment_tags"

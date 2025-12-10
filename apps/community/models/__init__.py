from .post_comment import PostComment
from .post_comment_tags import PostCommentTags
# 순환참조때문에 생기는 빨간 밑줄
# 장고에서는 문제 없는데 파이참에서는 오류로 인식해서 생긴다고 함
# 수정하려면 post_comment_tags.py 에서 PostComment을 import하지 말고 문자열 참조로 바꿔버리기
# ex) comment = models.ForeignKey(PostComment, on_delete=models.CASCADE)
#  -> comment = models.ForeignKey("community.PostComment", on_delete=models.CASCADE)


from django.urls import path

from apps.qna.views.answer.answers import (
    AnswerAdoptAPIView,
    AnswerDetailAPIView,
    AnswerListAPIView,
)
from apps.qna.views.answer.comments import (
    CommentDetailAPIView,
    CommentListAPIView,
)
from apps.qna.views.answer.images import AnswerImagePresignedURLView

app_name = "answers"

urlpatterns = [
    # ---답변---
    # 특정질문의 답변 목록 조회/ 답변 생성
    path(
        "questions/<int:question_id>/answers/",
        AnswerListAPIView.as_view(),
        name="answer_list",
    ),
    # 답변 상세조회/ 수정/ 삭제
    path(
        "questions/<int:question_id>/answers/<int:pk>/",
        AnswerDetailAPIView.as_view(),
        name="answer_detail",
    ),
    # 답변채택 (toggle)
    path(
        "questions/<int:question_id>/answers/<int:pk>/adopt/",
        AnswerAdoptAPIView.as_view(),
        name="answer_adopt",
    ),
    # ---댓글---
    # 답변의 댓글 목록 조회/ 생성
    path(
        "questions/<int:question_id>/answers/<int:answer_id>/comments/",
        CommentListAPIView.as_view(),
        name="comment_list",
    ),
    # 댓글 상세조회/ 수정/ 삭제
    path(
        "questions/<int:question_id>/answers/<int:answer_id>/comments/<int:pk>/",
        CommentDetailAPIView.as_view(),
        name="comment_detail",
    ),
    # ---이미지---
    # 답변 이미지 업로드용 presigned url발급
    path(
        "questions/<int:question_id>/answers/<int:answer_id>/images/presigned-url/",
        AnswerImagePresignedURLView.as_view(),
        name="answer_image_presigned_url",
    ),
]

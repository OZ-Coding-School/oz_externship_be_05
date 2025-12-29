from django.urls import path

from apps.qna.views.common.presigned_url_view import PresignedUploadAPIView
from apps.qna.views.question.question_api import QuestionAPIView
from apps.qna.views.question.question_detail import QuestionDetailAPIView

urlpatterns = [
    path("questions", QuestionAPIView.as_view(), name="questions"),
    path("questions/<int:question_id>", QuestionDetailAPIView.as_view(), name="question_detail"),
    # 이미지 업로드용
    path("upload/presigned-url/", PresignedUploadAPIView.as_view(), name="presigned_url"),
]

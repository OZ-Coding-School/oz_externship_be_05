from django.urls import path

from apps.qna.views.question.presigned_url_view import PresignedUploadAPIView
from apps.qna.views.question.question_api import QuestionAPIView
from apps.qna.views.question.question_detail import QuestionDetailAPIView
from apps.qna.views.question.question_detail import QuestionAIAnswerAPIView

urlpatterns = [
    path("questions", QuestionAPIView.as_view(), name="questions"),
    path("questions/<int:question_id>", QuestionDetailAPIView.as_view(), name="question_detail"),
    path("questions/<int:question_id>/ai-answer", QuestionAIAnswerAPIView.as_view(), name="question_ai_answer"),
    # 이미지 업로드용
    path("questions/presigned-url/", PresignedUploadAPIView.as_view(), name="question_presigned_url"),
]

from django.urls import path

from apps.qna.spec.answer.views import AnswerCreateSpecAPIView

urlpatterns = [
    path("questions/<int:question_id>/answers/", AnswerCreateSpecAPIView.as_view(), name="answer_create_spec"),
]

# Spec API는 명세 노출 목적이라 생성만 정의했고, 조회·수정·삭제는 실 API에서 구현할 예정입니다.

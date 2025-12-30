from rest_framework.views import APIView

from apps.qna.permissions.answer.answer_permission import AnswerAccessPermission


class BaseAnswerAPIView(APIView):
    permission_classes = [AnswerAccessPermission]

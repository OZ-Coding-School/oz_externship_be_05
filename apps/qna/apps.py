from django.apps import AppConfig


class QnaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"

    name = "apps.qna"

    """
    앱 로딩 시 시그널/태스크 모듈 등록
    Signal: import 되는 순간 등록
    celery worker: task import 해야 task registry 등록됨
    """

    def ready(self) -> None:
        import apps.qna.utils.ai_answer_signals
        import apps.qna.utils.ai_answer_tasks

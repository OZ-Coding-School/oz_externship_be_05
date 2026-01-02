from django.core.management.base import BaseCommand
from typing import Any
from apps.qna.models import Answer, AnswerComment, Question
from apps.qna.models.question.question_category import QuestionCategory
from apps.user.models import User


class Command(BaseCommand):
    help = "지정된 user_id(4번(학생) 질문, 6/7번(조교/어드민) 답변)를 기반으로 Q&A 목데이터를 생성합니다."

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            # 1. 유저 조회 (질문자: 4번, 답변자: 6번, 7번)
            questioner = User.objects.get(id=4)
            answerer_1 = User.objects.get(id=9)
            answerer_2 = User.objects.get(id=7)

            # 카테고리 (첫 번째 카테고리 사용)
            category = QuestionCategory.objects.first()

            if not category:
                self.stdout.write(self.style.ERROR("카테고리가 데이터베이스에 없습니다."))
                return

            # 2. 질문 생성 (작성자: 4번)
            q = Question.objects.create(
                author=questioner,
                category=category,
                title="4번 수강생의 테스트 질문입니다.",
                content="삭제 테스트를 위해 4번 유저가 작성한 질문 본문입니다.",
            )

            # 3. 첫 번째 답변 생성 (작성자: 6번)
            a1 = Answer.objects.create(
                question=q, author=answerer_1, content="9번 유저가 작성한 첫 번째 테스트 답변입니다."
            )

            # 4. 두 번째 답변 생성 (작성자: 7번)
            a2 = Answer.objects.create(
                question=q, author=answerer_2, content="7번 유저가 작성한 두 번째 테스트 답변입니다."
            )

            # 5. 답변에 대한 댓글 생성
            AnswerComment.objects.create(
                answer=a1, author=questioner, content="질문자(4번)가 9번 답변에 단 댓글입니다."
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"성공적으로 데이터를 생성했습니다.\n"
                    f"- 질문(ID:{q.id}): 작성자 4번({questioner.nickname})\n"
                    f"- 답변 1: 작성자 9번({answerer_1.nickname})\n"
                    f"- 답변 2: 작성자 7번({answerer_2.nickname})"
                )
            )

        except User.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"오류: 지정된 ID의 유저를 찾을 수 없습니다. ({e})"))

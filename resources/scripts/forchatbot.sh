#!/bin/bash
set -euo pipefail

DJANGO_CONTAINER="django"

read -p "이메일을 입력하세요: " EMAIL
read -s -p "비밀번호를 입력하세요: " PASSWORD

read -p "질문 카테고리를 입력하세요(ex. 백엔드): " QUESTION_CATEGORY
read -p "질문 제목을 입력하세요: " TITLE
read -p "질문 상세내역을 입력하세요: " CONTENT
echo ""

NAME="Anthony"
BIRTHDAY="2006-02-04"
GENDER="M"
PHONE_NUMBER="01012345678"

docker exec -i "$DJANGO_CONTAINER" python manage.py shell -c "
from apps.user.models import User, RoleChoices
from apps.qna.models.question.question_category import QuestionCategory
from apps.qna.models.question.question_base import Question
from apps.chatbot.models.chatbot_sessions import ChatbotSession, ChatModel

email='''$EMAIL'''.strip().lower()
pw='''$PASSWORD'''
name='''$NAME'''
birthday='''$BIRTHDAY'''
gender='''$GENDER'''
phone='''$PHONE_NUMBER'''
input_category='''$QUESTION_CATEGORY'''
title='''$TITLE'''
content='''$CONTENT'''

if User.objects.filter(email=email).exists():
    print('이미 존재하는 이메일입니다:', email)
else:
    user = User.objects.create_user(
        email=email,
        password=pw,
        name=name,
        role=RoleChoices.ST,
        birthday=birthday,
        gender=gender,
        phone_number=phone,
    )
    print('생성 완료:', user.id, user.email)

question_category = QuestionCategory.objects.create(
    name=input_category,
)
print('질문 카테고리 객체 생성: ', question_category.id, question_category.name)

if Question.objects.filter(title=title).exists():
    print('이미 존재하는 질문입니다:', question)
else:
    question = Question.objects.create(
          author=user,
          category=question_category,
          title=title,
          content=content,
    )
    print('생성 완료:', question.author_id, question.title, question.content)

test_session = ChatbotSession.objects.create(
    user=user,
    question=question,
    title='테스트 세션',
    using_model=ChatModel.GEMINI,
)
print('생성 완료:', test_session.id, test_session.title, test_session.using_model)
"
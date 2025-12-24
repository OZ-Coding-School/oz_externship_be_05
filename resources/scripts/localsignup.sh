#!/bin/bash
set -euo pipefail

DJANGO_CONTAINER="django"

read -p "이메일을 입력하세요: " EMAIL
read -s -p "비밀번호를 입력하세요: " PASSWORD
echo ""

NAME="한율"
BIRTHDAY="2006-02-04"
GENDER="M"
PHONE_NUMBER="01012345678"

docker exec -i "$DJANGO_CONTAINER" python manage.py shell -c "
from apps.user.models import User
email='''$EMAIL'''.strip().lower()
pw='''$PASSWORD'''
name='''$NAME'''
birthday='''$BIRTHDAY'''
gender='''$GENDER'''
phone='''$PHONE_NUMBER'''

if User.objects.filter(email=email).exists():
    print('이미 존재하는 이메일입니다:', email)
else:
    user = User.objects.create_user(
        email=email,
        password=pw,
        name=name,
        birthday=birthday,
        gender=gender,
        phone_number=phone,
    )
    print('생성 완료:', user.id, user.email)
"
from __future__ import annotations

from datetime import date, timedelta

from django.utils import timezone

from apps.courses.models.cohorts_models import Cohort
from apps.courses.models.courses_models import Course
from apps.user.models import User


def make_user(
    *,
    email: str = "u@test.com",
    password: str = "pass1234!!",
    name: str = "name",
    nickname: str = "nick",
    phone_number: str = "01012345678",
    gender: str = "M",
    birthday: date = date(2000, 1, 1),
    role: str = "U",
    is_active: bool = True,
) -> User:
    user = User.objects.create_user(
        email=email,
        password=password,
        name=name,
        nickname=nickname,
        phone_number=phone_number,
        gender=gender,
        birthday=birthday,
        role=role,
        is_active=is_active,
    )
    return user


def make_course(*, name: str = "Backend", tag: str = "BE", description: str = "desc") -> Course:
    return Course.objects.create(name=name, tag=tag, description=description)


def make_cohort(
    *,
    course: Course,
    number: int = 1,
    max_student: int = 30,
) -> Cohort:
    today = timezone.now().date()
    return Cohort.objects.create(
        course=course,
        number=number,
        max_student=max_student,
        start_date=today,
        end_date=today + timedelta(days=30),
    )

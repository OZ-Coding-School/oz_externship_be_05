from datetime import date
from typing import Final

from apps.courses.models.cohorts_models import Cohort
from apps.courses.models.courses_models import Course
from apps.user.models import User


def make_user(
    *,
    email: str,
    password: str,
    name: str,
    nickname: str,
    phone_number: str,
    gender: str,
    birthday: date,
    role: str,
    is_active: bool,
) -> User:
    return User.objects.create_user(
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


def make_course(*, name: str, tag: str, description: str) -> Course:
    return Course.objects.create(name=name, tag=tag, description=description)


def make_cohort(
    *,
    course: Course,
    number: int,
    max_student: int,
    start_date: date,
    end_date: date,
) -> Cohort:
    return Cohort.objects.create(
        course=course,
        number=number,
        max_student=max_student,
        start_date=start_date,
        end_date=end_date,
    )

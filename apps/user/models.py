from __future__ import annotations

from typing import Any

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models.cohorts_models import Cohort
from apps.user.utils.nickname import generate_nickname


class UserManager(BaseUserManager["User"]):
    def create_user(self, email: str, password: str, name: str, **extra_fields: Any) -> "User":
        if not email:
            raise ValueError("이메일은 필수입니다.")
        if not password:
            raise ValueError("비밀번호는 필수입니다.")
        if not name:
            raise ValueError("사용자명은 필수입니다.")
        if not extra_fields.get("nickname"):
            nickname: str = generate_nickname()
            ma: int = 5  # max attempts
            a: int = 0  # attempts
            while User.objects.filter(nickname=nickname).exists():
                nickname = generate_nickname()
                a += 1
                if a >= ma:
                    raise ValueError("자동 닉네임 생성에 실패했습니다. 직접 닉네임을 입력해주세요.")
            extra_fields["nickname"] = nickname
        email = self.normalize_email(email)
        user: "User" = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, name: str, **extra_fields: Any) -> "User":
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("role", RoleChoices.AD)
        return self.create_user(email, password, name, **extra_fields)


class GenderChoices(models.TextChoices):
    MALE = "M", "MALE"
    FEMALE = "F", "FEMALE"


class RoleChoices(models.TextChoices):
    TA = "TA", "Teaching Assistant"
    LC = "LC", "Learning Coach"
    OM = "OM", "Office Manager"
    ST = "ST", "Student"
    AD = "AD", "Administrator"
    USER = "U", "User"


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=30)
    nickname = models.CharField(max_length=15, unique=True)
    phone_number = models.CharField(max_length=20)
    gender = models.CharField(choices=GenderChoices.choices, max_length=1)
    birthday = models.DateField()
    profile_image_url = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    role = models.CharField(choices=RoleChoices.choices, max_length=2, default=RoleChoices.USER)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "birthday"]

    class Meta:
        db_table = "users"


class SocialProvider(models.TextChoices):
    NAVER = "N", "naver"
    KAKAO = "K", "kakao"


class SocialUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(choices=SocialProvider.choices, max_length=5)
    provider_id = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "social_users"


class EnrollmentStatus(models.TextChoices):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class StudentEnrollmentRequest(TimeStampedModel):
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(choices=EnrollmentStatus.choices, default=EnrollmentStatus.PENDING)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "student_enrollment_requests"


class CohortStudent(TimeStampedModel):
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "cohort_students"


class TrainingAssistant(TimeStampedModel):
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "training_assistants"


class OperationManager(TimeStampedModel):
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "operation_managers"


class LearningCoach(TimeStampedModel):
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "learning_coachs"


class WithdrawalReason(models.TextChoices):
    GRADUATION = "GRADUATION", "졸업 및 수료"
    TRANSFER = "TRANSFER", "편입 및 전학"
    NO_LONGER_NEEDED = "NO_LONGER_NEEDED", "더 이상 필요하지 않음"
    SERVICE_DISSATISFACTION = "SERVICE_DISSATISFACTION", "서비스 불만족"
    PRIVACY_CONCERN = "PRIVACY_CONCERN", "개인정보 보호 우려"
    OTHER = "OTHER", "기타"


class Withdrawal(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(choices=WithdrawalReason.choices)
    reason_detail = models.TextField()
    due_date = models.DateField()

    class Meta:
        db_table = "withdrawals"

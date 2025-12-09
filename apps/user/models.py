from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("이메일은 필수입니다.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class GenderChoices(models.TextChoices):
    MALE = 'M', 'MALE'
    FEMALE = 'F', 'FEMALE'

class RoleChoices(models.TextChoices):
    TA = 'TA', 'teaching Assistant'
    LC = 'LC', 'Learning Coach'
    OM = 'OM', 'Office Manager'
    ST = 'ST', 'Student'
    AD = 'AD', 'Administrator'
    USER = 'U', 'User'

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=30)
    nickname = models.CharField(max_length=10, unique=True)
    phone_num = models.CharField(max_length=20)
    gender = models.CharField(choices=GenderChoices.choices, max_length=6)
    birthday = models.DateField()
    profile_image_url = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname", "name"]

    class Meta:
        db_table = "users"

class SocialProvider(models.TextChoices):
    NAVER = 'N', 'naver'
    KAKAO = 'K', 'kakao'

class SocialUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(choices=SocialProvider.choices, max_length=5)
    provider_id = models.CharField(max_length=255)
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

def generate_nickname():
    import random
    adjectives = ['빠른', '영리한', '용감한', '친절한', '멋진', '귀여운', '강한', '현명한', '행복한', '빛나는', '신비한', '용감무쌍한', '자유로운', '창의적인', '열정적인', '지혜로운', '충직한', '사려깊은', '유쾌한', '명랑한', '하츠네', '활기찬', '상냥한', '다정한', '사랑스러운', '쿨한', '섬세한', '용맹한', '담대한', '민첩한', '영원한']
    objects = ['호랑이', '토끼', '독수리', '사자', '여우', '미쿠', '펭귄', '코끼리', '원숭이', '고양이', '강아지', '판다', '기린', '악어', '돌고래', '캥거루', '코알라', '부엉이', '늑대', '치타', '코뿔소','테토', '루카', '메이코', '멋쟁이', '천사', '마법사', '기사', '탐험가', '모험가', '연금술사', '무사', '닌자', '해적', '왕자', '공주', '용사', '전사', '마도사', '성기사', '암살자', '궁수', '사제', '주술사', '무희', '음유시인', '회사원', '학생', '선생님', '의사', '간호사', '엔지니어', '디자이너', '개발자', '작가', '화가', '요리사', '음악가', '배우', '운동선수', '과학자', '탐험가', '오타쿠', '게이머', '댄서', '모델', '사진사', '여행가', '요가강사', '트레이너', '코치', '멘토', '상담사', '심리학자', '철학자', '역사학자', '언어학자', '경제학자', '정치학자', '사회학자', '인류학자', '지리학자', '천문학자', '물리학자', '화학자', '생물학자', '지질학자', '프로게이머']
    return f"{random.choice(adjectives)}{random.choice(objects)}{random.randint(1, 9999)}"

class UserManager(BaseUserManager):
    def create_user(self, email, password, name, **extra_fields):
        if not email:
            raise ValueError("이메일은 필수입니다.")
        if not password:
            raise ValueError("비밀번호는 필수입니다.")
        if not name:
            raise ValueError("사용자명은 필수입니다.")
        if not extra_fields.get("nickname"):
            nickname = generate_nickname()
            ma = 100 # max attempts
            a = 0 # attempts
            while User.objects.filter(nickname=nickname).exists():
                nickname = generate_nickname()
                a += 1
                if a >= ma:
                    raise ValueError("자동 닉네임 생성에 실패했습니다. 직접 닉네임을 입력해주세요.")
            extra_fields["nickname"] = nickname
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password, name, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("role", RoleChoices.AD)
        return self.create_user(email, password, name, **extra_fields)

class GenderChoices(models.TextChoices):
    MALE = 'M', 'MALE'
    FEMALE = 'F', 'FEMALE'

class RoleChoices(models.TextChoices):
    TA = 'TA', 'Teaching Assistant'
    LC = 'LC', 'Learning Coach'
    OM = 'OM', 'Office Manager'
    ST = 'ST', 'Student'
    AD = 'AD', 'Administrator'
    USER = 'U', 'User'

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=30)
    nickname = models.CharField(max_length=25, unique=True)
    phone_num = models.CharField(max_length=20)
    gender = models.CharField(choices=GenderChoices.choices, max_length=1)
    birthday = models.DateField()
    profile_image_url = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    role = models.CharField(choices=RoleChoices.choices, max_length=2, default=RoleChoices.USER)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        db_table = "users"

class SocialProvider(models.TextChoices):
    NAVER = 'N', 'naver'
    KAKAO = 'K', 'kakao'

class SocialUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(choices=SocialProvider.choices, max_length=5)
    provider_id = models.CharField(max_length=255, unique=True)
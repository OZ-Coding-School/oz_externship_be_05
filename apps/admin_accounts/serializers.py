from rest_framework import serializers

from apps.user.models import User
from apps.courses.models.cohorts_models import Cohort
from apps.courses.models.courses_models import Course

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

# 어드민 페이지 회원 목록 조회 API 시리얼라이저
class AdminAccountListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "nickname",
            "name",
            "birthday",
            "status",
            "role",
            "created_at",
        )

# 어드민 페이지 회원 정보 상세 조회 API 시리얼라이저
class CourseMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "name", "tag")

class CohortMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cohort
        fields = ("id", "number", "status", "start_date", "end_date")

class AdminAccountRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "gender",
            "status",
            "role",
            "profile_img_url",
            "assigned_courses",
            "created_at",
        )

    def get_assigned_courses(self, obj: User):
        result = []
        for cs in obj.cohort_students.all():
            cohort = cs.cohort
            if not cohort:
                continue
            course = cohort.course
            result.append({
                "course": CourseMiniSerializer(course).data,
                "cohort": CohortMiniSerializer(cohort).data,
            })
        return result

# 어드민 페이지 회원 정보 수정 API 시리얼라이저
class AdminAccountUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "gender",
            "status",
            "profile_img_url",
        )

# 수정 응답 시리얼라이저
class AdminAccountResponseSerialzier(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id"
            "email"
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "gender",
            "status",
            "profile_img_url",
            "updated_at"
        )

# 어드민 페이지 권한 변경 API 시리얼라이저
ROLE_USER = {"U", "AD"}
ROLE_COHORT = {"TA", "ST"}
ROLE_COURSES = {"OM", "LC"}

class AdminAccountRoleUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["U", "AD", "TA", "ST", "OM", "LC"])
    cohort_id = serializers.IntegerField(required=False, allow_null=True)
    assigned_courses = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=False,
    )

    def validate(self, attrs):
        role = attrs["role"]
        cohort_id_present = "cohort_id" in attrs and attrs.get("cohort_id") is not None
        courses_present =  attrs in "assigned_courses"

        # 유저,어드민은 role만 수정 가능
        if role in ROLE_USER:
            if cohort_id_present or courses_present:
                raise serializers.ValidationError({
                    "detail": "USER/ADMIN은 role만 변경 가능합니다.",
                    "allowed_fields": ["role"],
                })
            return attrs

        # 학생/조교는 cohort_id 필수, assigned_courses 수정 금지
        if role in ROLE_COHORT:
            if not cohort_id_present:
                raise serializers.ValidationError({"cohort_id": ["학생/조교 권한으로 변경 시 필수 필드입니다."]})
            if courses_present:
                raise serializers.ValidationError({"assigned_courses": ["학생/조교 권한으로 변경할 수 없는 필드입니다."]})
            return attrs

        # 러닝코치/운영매니저는 assigned_courses 필수, cohort_id 수정 금지
        if role in ROLE_COURSES:
            if not courses_present:
                raise serializers.ValidationError({"assigned_courses": ["러닝코치/운영매니저 권한으로 변경 시 필수 필드입니다."]})
            if cohort_id_present:
                raise serializers.ValidationError({"cohort_id": ["러닝코치/운영매니저 권한으로 변경할 수 없는 필드입니다."]})
            return attrs

        return attrs


# 수강생 목록 조회 API SR
class CourseMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "name", "tag")

class CohortMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cohort
        fields = ("id", "number")

class AdminAccountStudentSerializer(serializers.Serializer):
    class Meta:
        model = Cohort
        fields = (
            "count",
            "next",
            "previous",
            "results",
            "created_at",
        )
    
    def get_results(self, obj:Cohort):
        results = []
        obj.


# 수강생 등록 요청 목록 조회 API SR
class AdminAccountStudentEnrollSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField()
    previous = serializers.CharField()

    

# 수강생 등록 요청 승인 API SR


# 수강생 등록 요청 거절 API SR
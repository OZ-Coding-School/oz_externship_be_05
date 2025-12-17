from rest_framework import serializers
from apps.user.models import User
from apps.admin_accounts.serializers.common import CourseMiniSerializer, CohortMiniSerializer

ROLE_USER = {"U", "AD"}
ROLE_COHORT = {"TA", "ST"}
ROLE_COURSES = {"OM", "LC"}

class AdminAccountListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id","email","nickname","name","birthday","status","role","created_at")

class AdminAccountRetrieveSerializer(serializers.ModelSerializer):
    assigned_courses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id","email","nickname","name","phone_number","birthday","gender",
            "status","role","profile_img_url","assigned_courses","created_at",
        )

    def get_assigned_courses(self, obj: User):
        result = []
        for cs in obj.cohort_students.all():
            cohort = cs.cohort
            if not cohort:
                continue
            result.append({
                "course": CourseMiniSerializer(cohort.course).data,
                "cohort": CohortMiniSerializer(cohort).data,
            })
        return result

class AdminAccountUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("nickname","name","phone_number","birthday","gender","status","profile_img_url")

class AdminAccountResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id","email","nickname","name","phone_number","birthday","gender",
            "status","profile_img_url","updated_at",
        )

class AdminAccountRoleUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["U","AD","TA","ST","OM","LC"])
    cohort_id = serializers.IntegerField(required=False, allow_null=True)
    assigned_courses = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=False)

    def validate(self, attrs):
        role = attrs["role"]
        cohort_id_present = "cohort_id" in attrs and attrs.get("cohort_id") is not None
        courses_present = "assigned_courses" in attrs and attrs.get("assigned_courses") is not None

        if role in ROLE_USER:
            if cohort_id_present or courses_present:
                raise serializers.ValidationError({"detail": "USER/ADMIN은 role만 변경 가능합니다.", "allowed_fields": ["role"]})
            return attrs

        if role in ROLE_COHORT:
            if not cohort_id_present:
                raise serializers.ValidationError({"cohort_id": ["학생/조교 권한으로 변경 시 필수 필드입니다."]})
            if courses_present:
                raise serializers.ValidationError({"assigned_courses": ["학생/조교 권한으로 변경할 수 없는 필드입니다."]})
            return attrs

        if role in ROLE_COURSES:
            if not courses_present:
                raise serializers.ValidationError({"assigned_courses": ["러닝코치/운영매니저 권한으로 변경 시 필수 필드입니다."]})
            if cohort_id_present:
                raise serializers.ValidationError({"cohort_id": ["러닝코치/운영매니저 권한으로 변경할 수 없는 필드입니다."]})
            return attrs

        return attrs
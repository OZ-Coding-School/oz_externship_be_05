from rest_framework import serializers
from apps.user.models import User
from apps.user.models.enrollment import StudentEnrollmentRequest
from .common import CourseMiniSerializer, CohortSimpleSerializer, UserMiniSerializer

class AdminAccountStudentSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    cohort = CohortSimpleSerializer(read_only=True)
    course = serializers.SerializerMethodField()

    class Meta:
        model = StudentEnrollmentRequest
        fields = ("id","user","cohort","course","status","created_at")

    def get_course(self, obj):
        cohort = getattr(obj, "cohort", None)
        course = getattr(cohort, "course", None) if cohort else None
        return CourseMiniSerializer(course).data if course else None

class AdminAccountStudentEnrollSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id","email","nickname","name","phone_number","birthday","gender","status")

class AdminAccountStudentEnrollAcceptSerializer(serializers.Serializer):
    detail = serializers.CharField(max_length=255)
    success = serializers.IntegerField()
    failed = serializers.IntegerField()

class AdminAccountStudentEnrollRejectRequestSerializer(serializers.Serializer):
    enrollments = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)

class AdminAccountStudentEnrollRejectResponseSerializer(serializers.Serializer):
    detail = serializers.CharField(max_length=255)
    success = serializers.IntegerField()
    failed = serializers.IntegerField()
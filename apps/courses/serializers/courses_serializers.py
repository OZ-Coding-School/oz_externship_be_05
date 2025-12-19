from rest_framework import serializers

from apps.courses.models import Cohort


class CourseCohortSerializer(serializers.ModelSerializer[Cohort]):
    course_name = serializers.ReadOnlyField(source="course.name")
    cohort_display = serializers.SerializerMethodField()

    class Meta:
        model = Cohort
        fields = [
            "id",
            "course",
            "course_name",
            "number",
            "cohort_display",
            "status",
        ]
        read_only_fields = [
            "id",
            "course",
            "number",
            "status",
        ]

    def get_cohort_display(self, obj: Cohort) -> str:
        return f"{obj.number}기"

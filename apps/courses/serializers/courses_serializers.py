from rest_framework import serializers

from apps.courses.models import Cohort, Course


class CohortSerializer(serializers.ModelSerializer[Cohort]):
    display = serializers.SerializerMethodField()

    class Meta:
        model = Cohort
        fields = [
            "id",
            "number",
            "display",
            "status",
        ]
        read_only_fields = [
            "id",
            "number",
            "status",
        ]

    def get_display(self, obj: Cohort) -> str:
        return f"{obj.number}기"


class CourseCohortsSerializer(serializers.ModelSerializer[Course]):
    cohorts = CohortSerializer(source="select_enable_cohorts", many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["id", "name", "cohorts"]

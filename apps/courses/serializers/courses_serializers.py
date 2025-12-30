from rest_framework import serializers

from apps.courses.models import Cohort, Course, Subject


class CourseSerializer(serializers.ModelSerializer[Course]):
    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "tag",
        ]


class CohortSerializer(serializers.ModelSerializer[Cohort]):
    class Meta:
        model = Cohort
        fields = ["id", "course_id", "number", "status"]


class SubjectSerializer(serializers.ModelSerializer[Subject]):
    class Meta:
        model = Subject
        fields = [
            "id",
            "course_id",
            "title",
            "status",
            "thumbnail_img_url",
        ]

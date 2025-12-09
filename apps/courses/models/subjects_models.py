from django.db import models

from apps.courses.models import Course


class SubjectChoices(models.TextChoices):
    Activated = "active"
    Deactivated = "deactivated"


class Subject(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=30)
    number_of_days = models.SmallIntegerField(max_length=2)
    number_of_hours = models.SmallIntegerField(max_length=3)
    thumbnail_img_url = models.URLField(null=True, blank=True)
    status = models.CharField(
        max_length=11,
        choices=SubjectChoices.choices,
    )
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Subjects"

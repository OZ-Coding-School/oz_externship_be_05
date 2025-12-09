from django.db import models

class StatusChoices(models.TextChoices):
    Activated = "active"
    Deactivated = "deactivated"

class Cohorts(models.Model):
    course_id = models.BigIntegerField()
    number = models.PositiveIntegerField()
    max_student = models.PositiveIntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    status = models.CharField(
        max_length=11,
        choices=StatusChoices.choices,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = 'cohorts'
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models.cohorts_models import Cohort
from apps.user.models.user import User


class TrainingAssistant(TimeStampedModel):
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "training_assistants"


class OperationManager(TimeStampedModel):
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "operation_managers"


class LearningCoach(TimeStampedModel):
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "learning_coachs"


class CohortStudent(TimeStampedModel):
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "cohort_students"

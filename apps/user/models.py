from django.db import models

# Create your models here.
class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30, null=False)
    nickname = models.CharField(max_length=10, null=False, unique=True)
    phone_number = models.CharField(max_length=15, unique=True, null=False)
    gender = models.CharField(max_length=6, null=False)
    
    profile_image_url = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True, null=False)
    hashed_password = models.CharField(max_length=130, null=False)
    
    birthday = models.DateField(null=False)
    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
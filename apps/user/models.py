from django.db import models
from django.db.models import CharField, DateField, DateTimeField, BooleanField, AutoField, EmailField

class User(models.Model):

    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        POLCLAIN = 'P', 'Polclain'
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN'
        STAFF = 'STAFF'
        USER = 'USER'
    
    id = AutoField(primary_key=True)
    name = CharField(max_length=30, null=False)
    nickname = CharField(max_length=10, null=False, unique=True)
    phone_number = CharField(max_length=20, unique=True, null=False)
    gender = CharField(max_length=6, choices = Gender.choices, null=False)
    role = CharField(max_length=10, choices=Role.choices, default=Role.USER)
    profile_image_url = CharField(max_length=255, null=True, blank=True)
    email = EmailField(unique=True, null=False)
    hashed_password = CharField(max_length=130, null=False)
    
    birthday = DateField(null=False)
    is_active = BooleanField(default=False)

    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
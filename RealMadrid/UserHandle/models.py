from django.db import models
from django.contrib.auth.models import AbstractUser

class Users(AbstractUser):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    password = models.CharField(max_length=255)  # Note: This should be hashed using Django's built-in mechanisms

    username = models.CharField(max_length=150, blank=True, null=True, unique=False)  # Make sure username is not unique if you intend to allow duplicates

    def __str__(self):
        return self.username or "No Username"
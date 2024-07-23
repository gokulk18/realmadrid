from django.db import models
from django.contrib.auth.models import AbstractUser
class Users(AbstractUser):

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    password = models.CharField(max_length=255)
       
    def str(self):
        return self.username
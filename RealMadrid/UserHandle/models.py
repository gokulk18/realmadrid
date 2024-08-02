from django.db import models
from django.contrib.auth.models import AbstractUser

class Users(AbstractUser):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    password = models.CharField(max_length=255)  # Note: This should be hashed using Django's built-in mechanisms

    username = models.CharField(max_length=150, blank=True, null=True, unique=False) 
    
    def __str__(self):
        return self.username or "No Username"
    
class Position(models.Model):
    position = models.CharField(max_length=255)

    def __str__(self):
        return self.position

class Player(models.Model):
    jersey_num = models.CharField(max_length=10)
    player_name = models.CharField(max_length=100)
    player_country = models.CharField(max_length=50)
    player_position = models.ForeignKey(Position, on_delete=models.CASCADE)
    player_role = models.CharField(max_length=50)
    player_image = models.ImageField(upload_to='player_images/')

    def __str__(self):
        return self.player_name
    

    
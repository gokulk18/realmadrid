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
    
class News(models.Model):
    title = models.CharField(max_length=255)  # Title with a maximum length of 255 characters
    description = models.TextField()  # For long paragraphs
    news_image = models.ImageField(upload_to='news_images/')  # File upload for images
    date_created = models.DateTimeField(auto_now_add=True)  # Automatically set when created
    
    def __str__(self):
        return self.title

class Category(models.Model):
    category_name = models.CharField(max_length=255,unique=True)
    
    def __str__(self):
        return self.category_name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sub_category_name = models.CharField(max_length=255,unique=True)
    
    def __str__(self):
        return self.sub_category_name

class Item(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, related_name='items', on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, related_name='items', on_delete=models.CASCADE, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    main_image = models.ImageField(upload_to='items/main/', null=True, blank=True)

    def __str__(self):
        return self.name

class ItemSize(models.Model):
    item = models.ForeignKey(Item, related_name='sizes', on_delete=models.CASCADE)
    size = models.CharField(max_length=50, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('item', 'size')

    def __str__(self):
        return f"{self.item.name} - {self.size}"

class ItemImage(models.Model):
    item = models.ForeignKey(Item, related_name='additional_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='items/additional/')

    def __str__(self):
        return f"Image for {self.item.name}"


class Cart(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.name}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.quantity} of {self.item.name} in cart for {self.cart.user.name}"
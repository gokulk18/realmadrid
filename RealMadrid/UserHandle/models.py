from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.crypto import get_random_string
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.utils import timezone
import json
from django.conf import settings
from .utils import VideoProcessor  # Import your existing ML utilities
import os
import numpy as np

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
    
    # New fields for basic info
    date_of_birth = models.DateField(null=True, blank=True)
    height = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)  # in meters
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # in kg
    
    # Statistics
    appearances = models.PositiveIntegerField(default=0)
    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    clean_sheets = models.PositiveIntegerField(default=0)  # for goalkeepers
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    
    # Additional info
    biography = models.TextField(blank=True)
    joined_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    
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

    def get_sizes_and_quantities(self):
        size_quantities = self.sizes.all()
        if size_quantities.exists():
            return [(sq.size, sq.quantity) for sq in size_quantities]
        else:
            # If no sizes, return a single tuple with None as size and total quantity
            total_quantity = self.sizes.aggregate(total=models.Sum('quantity'))['total'] or 0
            return [(None, total_quantity)]

class ItemSize(models.Model):
    item = models.ForeignKey(Item, related_name='sizes', on_delete=models.CASCADE)
    size = models.CharField(max_length=50, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('item', 'size')

    def __str__(self):
        return f"{self.item.name} - {self.size or 'No Size'}: {self.quantity}"

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

    def get_available_quantity(self):
        if self.size:
            item_size = ItemSize.objects.filter(item=self.item, size=self.size).first()
            return item_size.quantity if item_size else 0
        else:
            return sum(size.quantity for size in self.item.sizes.all())
    

class Wishlist(models.Model):
    user = models.OneToOneField(Users, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist for {self.user.name}"

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wishlist', 'item')

    def __str__(self):
        return f"{self.item.name} in wishlist for {self.wishlist.user.name}"
    
    
    
class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Confirmed')
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    apartment = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=20)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        return f"ORD-{get_random_string(16).upper()}"

    def __str__(self):
        return f"Order {self.order_number} for {self.full_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.quantity} of {self.item.name} in Order {self.order.order_number}"

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded')
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, unique=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.transaction_id} for Order {self.order.order_number}"

class Shipping(models.Model):
    SHIPPING_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Packed', 'Packed'),
        ('Shipped', 'Shipped'),
        ('In Transit', 'In Transit'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered')
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    shipping_method = models.CharField(max_length=100)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    carrier = models.CharField(max_length=100, blank=True, null=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=SHIPPING_STATUS_CHOICES, default='Pending')
    packed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    out_for_delivery_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Shipping for Order {self.order.order_number}"

    def get_tracking_url(self):
        if self.carrier and self.tracking_number:
            # This is a simplified example. You'll need to implement logic for different carriers
            if self.carrier.lower() == 'ups':
                return f"https://www.ups.com/track?tracknum={self.tracking_number}"
            elif self.carrier.lower() == 'fedex':
                return f"https://www.fedex.com/fedextrack/?trknbr={self.tracking_number}"
            # Add more carriers as needed
        return None
    

class Stand(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name


class Section(models.Model):
    name = models.CharField(max_length=100)
    stand = models.ForeignKey(Stand, on_delete=models.CASCADE, related_name='sections')
    seats = models.JSONField(default=list)  # Store seat numbers as a JSON list
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ('stand', 'name')  # Ensure unique section names per stand

    def __str__(self):
        return f"{self.stand.name} - {self.name}"


class Match(models.Model):
    match_id = models.CharField(max_length=100, unique=True)
    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    utc_date = models.DateTimeField()
    ist_date = models.DateTimeField()
    competition = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    venue = models.CharField(max_length=100, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} on {self.ist_date}"

    class Meta:
        ordering = ['utc_date']

class TicketOrder(models.Model):
    ORDER_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Payment_Initiated', 'Payment Initiated'),
        ('Confirmed', 'Confirmed'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled')
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    booking_fee = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='Pending')
    razorpay_order_id = models.CharField(max_length=200, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_deadline = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        if not self.payment_deadline and self.status == 'Pending':
            # Set payment deadline to 15 minutes from creation
            self.payment_deadline = timezone.now() + timezone.timedelta(minutes=15)
        super().save(*args, **kwargs)

    def generate_order_number(self):
        # Generate a unique order number
        prefix = 'TKT'
        random_str = get_random_string(12, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        return f"{prefix}-{random_str}"

    def __str__(self):
        return f"Order {self.order_number} - {self.status}"

class TicketItem(models.Model):
    order = models.ForeignKey(TicketOrder, related_name='tickets', on_delete=models.CASCADE)
    stand = models.ForeignKey(Stand, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    seat_number = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=False)

    class Meta:
        unique_together = ('order', 'stand', 'section', 'seat_number')

    def __str__(self):
        return f"Ticket for {self.order.match} - {self.stand} {self.section} Seat {self.seat_number}"

class TicketPayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Initiated', 'Initiated'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded')
    ]

    ticket_order = models.OneToOneField(TicketOrder, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50)
    razorpay_payment_id = models.CharField(max_length=200, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=200, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=500, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, unique=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment for {self.ticket_order.order_number} - {self.status}"

class QuizQuestion(models.Model):
    question_text = models.TextField()
    options = models.JSONField()  # Use JSONField to store options as a list
    correct_answers = models.JSONField()  # Store correct answers as a list of indices

    def __str__(self):
        return self.question_text



class UploadedImage(models.Model):
    image = models.ImageField(upload_to='jigsaw_images/')  # Adjust the upload path as needed
    uploaded_at = models.DateTimeField(auto_now_add=True)


class IdentifyPlayer(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='guess_players/')

    def __str__(self):
        return self.name

class PlayerCredentials(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.player.player_name}'s credentials"

class PlayerTask(models.Model):
    TASK_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('evaluated', 'Evaluated'),
    )
    
    EXERCISE_TYPES = (
        ('pushup', 'Push-Ups'),
        ('squat', 'Squats'),
        ('jump', 'Jumps'),
        ('sprint', 'Sprints'),
        ('burpee', 'Burpees'),
        ('lunge', 'Lunges'),
        ('other', 'Other'),
    )
    
    player = models.ForeignKey(Player, related_name='tasks', on_delete=models.CASCADE)
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPES, default='other')
    repetitions = models.IntegerField(help_text="Number of repetitions to perform", default=0)
    instructions = models.TextField(blank=True, null=True)
    due_date = models.DateField(default=timezone.now)
    assigned_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='pending')
    
    def __str__(self):
        return f"{self.player.player_name} - {self.get_exercise_type_display()} x{self.repetitions}"

    def get_latest_video(self):
        """Get the most recent video submission for this task"""
        return self.videos.order_by('-uploaded_at').first()

    def has_video(self):
        """Check if this task has any video submissions"""
        return self.videos.exists()

    class Meta:
        ordering = ['-assigned_date']

class PlayerAchievement(models.Model):
    player = models.ForeignKey(Player, related_name='achievements', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.player.player_name} - {self.title}"

class PlayerHistory(models.Model):
    player = models.ForeignKey(Player, related_name='history', on_delete=models.CASCADE)
    club = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    appearances = models.PositiveIntegerField(default=0)
    goals = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.player.player_name} at {self.club}"

class SeasonStats(models.Model):
    player = models.ForeignKey(Player, related_name='season_stats', on_delete=models.CASCADE)
    season = models.CharField(max_length=9)  # e.g., "2023/2024"
    competition = models.CharField(max_length=100)  # e.g., "LaLiga", "Champions League"
    appearances = models.PositiveIntegerField(default=0)
    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    minutes_played = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('player', 'season', 'competition')
    
    def __str__(self):
        return f"{self.player.player_name} - {self.season} {self.competition}"

class PlayerVideo(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    )
    
    task = models.ForeignKey(PlayerTask, on_delete=models.CASCADE, related_name='videos')
    player = models.ForeignKey(
        Player, 
        on_delete=models.CASCADE, 
        related_name='videos'
    )
    video = models.FileField(
        upload_to='player_videos/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp4', 'avi', 'mov', 'wmv']
            )
        ]
    )
    processed_video = models.FileField(
        upload_to='processed_videos/', 
        null=True, 
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    trainer_comment = models.TextField(null=True, blank=True)
    processing_progress = models.FloatField(default=0)
    error_message = models.TextField(blank=True, null=True)
    evaluation_data = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='pending'
    )

    class Meta:
        ordering = ['-uploaded_at']
        get_latest_by = 'uploaded_at'

    def __str__(self):
        return f"Video by {self.player.player_name} for {self.task}"

    def get_video_url(self):
        """Get the appropriate video URL (processed if available, otherwise original)"""
        if self.processed_video:
            return self.processed_video.url
        return self.video.url if self.video else None

    def get_duration(self):
        """Get video duration in seconds (requires installing moviepy)"""
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(self.video.path)
            duration = clip.duration
            clip.close()
            return duration
        except Exception as e:
            return None

    def get_file_size(self):
        """Get video file size in MB"""
        try:
            return round(self.video.size / (1024 * 1024), 2)
        except Exception as e:
            return None

    def evaluate_video(self):
        try:
            if not self.video:
                return {
                    'success': False,
                    'error': 'No video file found'
                }

            video_path = self.video.path
            
            # Get exercise type from task
            exercise_type = self.task.exercise_type if hasattr(self.task, 'exercise_type') else 'general'
            target_reps = self.task.repetitions if hasattr(self.task, 'repetitions') else 0

            # Import your video processor
            from .utils import VideoProcessor
            processor = VideoProcessor()

            # Process based on exercise type
            if exercise_type == 'pushup':
                result = processor.evaluate_pushup(video_path, target_reps)
            elif exercise_type == 'squat':
                result = processor.evaluate_squat(video_path, target_reps)
            elif exercise_type == 'running':
                result = processor.evaluate_running(video_path)
            else:
                result = processor.evaluate_general_movement(video_path)

            if not result:
                return {
                    'success': False,
                    'error': 'Video processing failed'
                }

            return {
                'success': True,
                'processed_video_path': result.get('processed_video_path'),
                'evaluation_data': result.get('metrics'),
                'feedback': result.get('metrics', {}).get('recommendations', ['Exercise completed'])[0]
            }

        except Exception as e:
            logger.error(f"Video evaluation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

class ItemVisualEmbedding(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name='visual_embedding')
    embedding = models.BinaryField()  # Store the image embedding as binary data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_embedding_array(self):
        return np.frombuffer(self.embedding, dtype=np.float32)

    def set_embedding_array(self, array):
        self.embedding = array.astype(np.float32).tobytes()

    def __str__(self):
        return f"Visual embedding for {self.item.name}"
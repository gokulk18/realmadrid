import razorpay  # Add this import for Razorpay integration
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from .models import Users, Position, Player, News, Category, SubCategory, Item, ItemImage, ItemSize, Cart, CartItem, Wishlist, WishlistItem, Order, OrderItem, Payment, Shipping, Stand, Section, Match, TicketOrder, TicketItem, TicketPayment, QuizQuestion, UploadedImage, IdentifyPlayer, PlayerCredentials
import random
from django.contrib.auth.hashers import make_password, check_password # For password hashing
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from django.http import JsonResponse
import logging
from django.views.decorators.cache import never_cache
from .models import Position
from .models import Player
from .models import News,Cart, CartItem
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .models import Category
from .models import SubCategory,ItemImage,Item,ItemSize,Wishlist, WishlistItem,Order, OrderItem, Shipping,Payment,Section
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from allauth.socialaccount.models import SocialAccount
from django.http import Http404
from django.db.models import Sum  # Add this import
from django.views.decorators.http import require_POST
import json
from django.views.decorators.csrf import csrf_protect
import requests
from django.shortcuts import render
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
import pytz
from django.utils import timezone
import http
from .models import Match
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import TicketOrder, TicketItem, Match, Stand, Section
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import viewsets
from .models import QuizQuestion , PlayerTask
import os
from django.core.files.storage import FileSystemStorage
from PIL import Image
from .models import UploadedImage  # Assuming you have a model for storing images
from .models import IdentifyPlayer
from django.utils.html import strip_tags
from .models import Player, SeasonStats, PlayerHistory, PlayerAchievement
import json
import uuid
from django.core.cache import cache
from .models import Match  # Adjust based on your actual models
from decimal import Decimal, ROUND_HALF_UP
from django.db import IntegrityError
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Order, TicketItem
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle, Image, Spacer
from reportlab.lib.units import cm, mm, inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode
from django.conf import settings
import os
from datetime import datetime
from PIL import Image as PILImage
import textwrap
from reportlab.lib.colors import HexColor
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from datetime import timedelta
import json
from collections import defaultdict
from .models import PlayerVideo, Player
from django.contrib.auth.decorators import login_required
from .models import Player, PlayerTask
from django.views.decorators.http import require_POST
import cv2
import numpy as np
from django.core.files.base import ContentFile
import tempfile
import os
from django.core.files.storage import default_storage
from django.conf import settings
import os
from celery import shared_task
import cv2
import numpy as np
import mediapipe as mp
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from PIL import Image
import torch
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights
from scipy.spatial.distance import cosine
from django.views.decorators.http import require_http_methods
from .models import ItemVisualEmbedding  # Add this import


def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_ticket_stats(request):
    # Fetch only home matches for Real Madrid
    matches = Match.objects.filter(home_team='Real Madrid CF').order_by('utc_date')
    selected_match = None
    context = {'matches': matches}
    
    if request.method == 'POST' and request.POST.get('match_id'):
        match_id = request.POST.get('match_id')
        try:
            selected_match = Match.objects.get(match_id=match_id)
            
            # Get all ticket orders for this match
            ticket_orders = TicketOrder.objects.filter(match=selected_match)
            
            # Get all stands in the venue
            stands = Stand.objects.all()
            
            # Calculate total seats available (from all sections in all stands)
            total_seats = 0
            for stand in stands:
                sections = Section.objects.filter(stand=stand)
                for section in sections:
                    total_seats += len(section.seats)
            
            # Calculate stats
            confirmed_orders = ticket_orders.filter(status='Confirmed')
            cancelled_orders = ticket_orders.filter(status='Cancelled')
            
            # Count tickets
            tickets_sold = TicketItem.objects.filter(order__in=confirmed_orders, is_available=True).count()
            cancelled_tickets = TicketItem.objects.filter(order__in=cancelled_orders).count()
            tickets_available = total_seats - tickets_sold
            
            # Calculate percentages
            tickets_sold_percentage = (tickets_sold / total_seats * 100) if total_seats > 0 else 0
            cancelled_percentage = (cancelled_tickets / (tickets_sold + cancelled_tickets) * 100) if (tickets_sold + cancelled_tickets) > 0 else 0
            available_percentage = (tickets_available / total_seats * 100) if total_seats > 0 else 0
            
            # Calculate revenue from ticket payments
            payments = TicketPayment.objects.filter(ticket_order__in=confirmed_orders, status='Completed')
            total_revenue = sum(payment.amount_paid for payment in payments)
            avg_ticket_price = (total_revenue / tickets_sold) if tickets_sold > 0 else 0
            
            # Get stand-wise booking data
            stand_stats = []
            stand_names = []
            tickets_sold_counts = []
            tickets_available_counts = []
            
            for stand in stands:
                # Get all sections for this stand
                sections = Section.objects.filter(stand=stand)
                
                # Calculate stand capacity
                stand_capacity = sum(len(section.seats) for section in sections)
                
                # Count sold tickets for this stand
                stand_sold = TicketItem.objects.filter(
                    order__in=confirmed_orders,
                    stand=stand,
                    is_available=True
                ).count()
                
                # Count cancelled tickets for this stand
                stand_cancelled = TicketItem.objects.filter(
                    order__in=cancelled_orders,
                    stand=stand
                ).count()
                
                # Calculate available tickets
                stand_available = stand_capacity - stand_sold
                
                # Calculate revenue for this stand
                stand_tickets = TicketItem.objects.filter(
                    order__in=confirmed_orders,
                    stand=stand,
                    is_available=True
                )
                stand_revenue = sum(ticket.price for ticket in stand_tickets)
                
                # Calculate percentage sold
                sold_percentage = (stand_sold / stand_capacity * 100) if stand_capacity > 0 else 0
                
                stand_stats.append({
                    'name': stand.name,
                    'capacity': stand_capacity,
                    'sold': stand_sold,
                    'sold_percentage': sold_percentage,
                    'available': stand_available,
                    'revenue': stand_revenue,
                    'cancelled': stand_cancelled
                })
                
                stand_names.append(stand.name)
                tickets_sold_counts.append(stand_sold)
                tickets_available_counts.append(stand_available)
            
            # Get sales trend data (last 30 days)
            today = timezone.now().date()
            thirty_days_ago = today - timedelta(days=30)
            
            # Initialize all dates in the range
            date_range = [(thirty_days_ago + timedelta(days=i)).strftime('%Y-%m-%d') 
                          for i in range((today - thirty_days_ago).days + 1)]
            
            # Count bookings per day
            daily_bookings = defaultdict(int)
            for booking in bookings.filter(booking_date__gte=thirty_days_ago, status='confirmed'):
                booking_date = booking.booking_date.strftime('%Y-%m-%d')
                daily_bookings[booking_date] += 1
            
            # Create the daily sales data list
            daily_sales = [daily_bookings.get(date, 0) for date in date_range]
            
            # Get ticket categories data
            ticket_categories = ['VIP', 'Premium', 'Standard', 'Economy']  # Example categories
            category_counts = []
            
            # Count bookings by category
            for category in ticket_categories:
                category_count = bookings.filter(
                    ticket_type=category, 
                    status='confirmed'
                ).count()
                category_counts.append(category_count)
            
            # Add all data to context
            context.update({
                'selected_match': selected_match,
                'tickets_sold': tickets_sold,
                'total_seats': total_seats,
                'tickets_available': tickets_available,
                'tickets_sold_percentage': tickets_sold_percentage,
                'available_percentage': available_percentage,
                'cancelled_tickets': cancelled_tickets,
                'cancelled_percentage': cancelled_percentage,
                'total_revenue': total_revenue,
                'avg_ticket_price': avg_ticket_price,
                'stand_stats': stand_stats,
                'stand_names': json.dumps(stand_names),
                'tickets_sold_counts': json.dumps(tickets_sold_counts),
                'tickets_available_counts': json.dumps(tickets_available_counts),
                'sales_dates': json.dumps(date_range),
                'daily_sales': json.dumps(daily_sales),
                'ticket_categories': json.dumps(ticket_categories),
                'category_counts': json.dumps(category_counts),
            })
            
        except Match.DoesNotExist:
            pass  # Handle case where match doesn't exist
    
    return render(request, 'admin_ticket_stats.html', context)




class CustomTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(timestamp)

token_generator = CustomTokenGenerator()


def player_view(request):
    positions = Position.objects.all()

    # Create a dictionary to hold players by position
    players_by_position = {}
    for position in positions:
        players_by_position[position.position] = Player.objects.filter(player_position=position)

    context = {}  # Initialize context dictionary

    if request.user.is_authenticated:
        user = request.user
        context.update({
            'user_name': user.username,
            'user_email': user.email,
            'user_phone': getattr(user, 'phone', None),  # Optional: if you have a phone field in the User model
        })
    elif 'user_id' in request.session:
        try:
            user = Users.objects.get(id=request.session['user_id'])
            context.update({
                'user_name': user.name,
                'user_email': user.email,
                'user_phone': user.phone,  # Add other user-specific details if needed
            })
        except Users.DoesNotExist:
            pass  # Handle the case where the user does not exist

    return render(request, 'player_view.html', {'players_by_position': players_by_position, **context})


def get_cart_items(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'User not logged in'}, status=401)
    
    user = get_object_or_404(Users, id=user_id)
    cart, created = Cart.objects.get_or_create(user=user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('item')
    
    items_data = []
    for cart_item in cart_items:
        available_quantity = cart_item.get_available_quantity()
        items_data.append({
            'id': cart_item.id,
            'name': cart_item.item.name,
            'price': float(cart_item.item.price),
            'quantity': cart_item.quantity,
            'size': cart_item.size,
            'image': cart_item.item.main_image.url if cart_item.item.main_image else '',
            'total': float(cart_item.item.price * cart_item.quantity),
            'available_quantity': available_quantity,
            'out_of_stock': available_quantity == 0,
            'quantity_exceeded': cart_item.quantity > available_quantity
        })
    
    return JsonResponse(items_data, safe=False)


def payment_success(request):
    return render(request,'payment_success.html')






from django.shortcuts import render
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
import pytz
import requests
from .models import Stand
from django.utils import timezone

def stadium(request, match_id):
    match = get_object_or_404(Match, match_id=match_id)
    
    # Use ist_date directly without formatting
    kickoff_time = match.ist_date

    stands = Stand.objects.all()
    stands_sections = {}
    for stand in stands:
        sections = Section.objects.filter(stand=stand)
        stands_sections[stand] = sections

    context = {
        'match': {
            'id': match.match_id,
            'home_team': match.home_team,
            'away_team': match.away_team,
            'competition': match.competition,
            'kickoff_time': kickoff_time,  # Use the ist_date directly
        },
        'stands_sections': stands_sections,
    }

    return render(request, 'stadium.html', context)



@csrf_exempt
def store_ticket_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            request.session['ticket_data'] = {
                'stand': data.get('stand'),
                'section': data.get('section'),
                'quantity': data.get('quantity'),
                'price': data.get('price'),
                'match_id': data.get('match_id'),
                'match_details': data.get('match_details')  # Add this line
            }
            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})



def trainer_index(request):
    return render(request,'trainer_index.html')


from django.http import JsonResponse
from django.shortcuts import render
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder

# Load the model and feature names
model = joblib.load("random_forest_model.joblib")
with open("feature_names.txt", "r") as f:
    feature_names = [line.strip() for line in f]

label_encoder = LabelEncoder()

def trainer_test(request):
    if request.method == 'POST':
        try:
            # Retrieve form data
            player_name = request.POST.get('playerName')
            distance_covered = float(request.POST.get('distanceCovered'))
            sprint_speed = float(request.POST.get('sprintSpeed'))  # Ensure this is in m/s
            heart_rate = float(request.POST.get('heartRate'))
            training_load = float(request.POST.get('trainingLoad'))
            recovery = float(request.POST.get('recovery'))
            match_minutes = float(request.POST.get('matchMinutes'))
            wellness = float(request.POST.get('wellness'))
            injury_status = request.POST.get('injuryStatus')

            # Prepare input data for prediction
            input_data = {
                'Distance Covered (km)': distance_covered,
                'Sprint Speed (m/s)': sprint_speed,  # Ensure this matches the CSV
                'Heart Rate (bpm)': heart_rate,
                'Injury Status': injury_status,
                'Training Load (min/week)': training_load,
                'Recovery Time (hours)': recovery,
                'Match Minutes Played': match_minutes,
                'Wellness Score': wellness
            }

            # Convert input data to DataFrame for prediction
            input_df = pd.DataFrame([input_data])

            # One-hot encode categorical features
            input_df = pd.get_dummies(input_df, columns=['Injury Status'], drop_first=True)

            # Ensure the input DataFrame has the same columns as the training data
            input_df = input_df.reindex(columns=feature_names, fill_value=0)

            # Debugging: Print the input DataFrame
            print("Input DataFrame for prediction:")
            print(input_df)

            # Make predictions
            prediction = model.predict(input_df)

            # Determine match fit status based on prediction
            match_fit_status = "Match Fit" if prediction[0] == 1 else "Not Match Fit"

            # Return prediction as JSON response
            return JsonResponse({'prediction': match_fit_status, 'player_name': player_name})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return render(request, 'trainer_test.html')


def schedule(request):
    api_key = 'dc93cd61f7a04a67be5652fc72195459'
    url = 'https://api.football-data.org/v4/teams/86/matches'  # Real Madrid's ID is 86
    headers = {'X-Auth-Token': api_key}

    response = requests.get(url, headers=headers)
    all_fixtures = response.json().get('matches', [])
 
    ist_timezone = pytz.timezone('Asia/Kolkata')
    current_time = timezone.now()

    for fixture in all_fixtures:
        utc_date = parse_datetime(fixture['utcDate'])
        # Check if this is a home game and has all required data
        if (utc_date and 
            fixture['homeTeam']['name'] == 'Real Madrid CF' and 
            'awayTeam' in fixture and 
            fixture['awayTeam'].get('name')):  # Add these checks
            
            if utc_date.tzinfo is None:
                utc_date = make_aware(utc_date)
            
            if utc_date > current_time:
                ist_date = utc_date.astimezone(ist_timezone)
                
                # Create or update the Match object in the database
                try:
                    Match.objects.update_or_create(
                        match_id=fixture['id'],
                        defaults={
                            'home_team': fixture['homeTeam']['name'],
                            'away_team': fixture['awayTeam']['name'],
                            'utc_date': utc_date,
                            'ist_date': ist_date,
                            'competition': fixture['competition']['name'],
                            'status': fixture['status'],
                            'venue': fixture.get('venue', 'Santiago Bernabéu'),  # Set default venue
                        }
                    )
                except Exception as e:
                    print(f"Error creating match: {e}")
                    continue

    # Fetch upcoming home fixtures from the database
    upcoming_home_fixtures = Match.objects.filter(
        home_team='Real Madrid CF',
        utc_date__gt=current_time
    ).order_by('utc_date')

    # Initialize user_tickets as None
    user_tickets = None

    # Get user's ticket bookings if they are logged in
    if request.user.is_authenticated:
        user = request.user
        user_tickets = TicketOrder.objects.filter(
            user=user,
            match__utc_date__gt=current_time
        ).select_related('match').prefetch_related('tickets')
        
        context = {
            'fixtures': upcoming_home_fixtures,
            'user_tickets': user_tickets,
            'user_name': user.username,
            'user_email': user.email,
            'user_phone': getattr(user, 'phone', None),
        }
    elif 'user_id' in request.session:
        try:
            user = Users.objects.get(id=request.session['user_id'])
            # Get ticket orders for the session user
            user_tickets = TicketOrder.objects.filter(
                user=user,
                match__utc_date__gt=current_time
            ).select_related('match').prefetch_related('tickets')
            
            context = {
                'fixtures': upcoming_home_fixtures,
                'user_tickets': user_tickets,
                'user_name': user.name,
                'user_email': user.email,
                'user_phone': user.phone,
            }
        except Users.DoesNotExist:
            context = {
                'fixtures': upcoming_home_fixtures,
            }
    else:
        context = {
            'fixtures': upcoming_home_fixtures,
        }

    return render(request, 'schedule.html', context)

@login_required
def cancel_ticket(request, order_id):
    """
    Show the ticket cancellation confirmation page
    """
    # Get the ticket order
    try:
        # Check if user is authenticated through Django auth
        if request.user.is_authenticated:
            order = get_object_or_404(TicketOrder, id=order_id, user=request.user)
        # Check if user is authenticated through session
        elif 'user_id' in request.session:
            user = Users.objects.get(id=request.session['user_id'])
            order = get_object_or_404(TicketOrder, id=order_id, user=user)
        else:
            messages.error(request, 'You must be logged in to cancel tickets.')
            return redirect('schedule')
    except TicketOrder.DoesNotExist:
        messages.error(request, 'Ticket order not found.')
        return redirect('schedule')
    
    # Check if the order is already cancelled
    if order.status == 'Cancelled':
        messages.error(request, 'This ticket has already been cancelled.')
        return redirect('schedule')
    
    # Calculate refund amount (75% of total price)
    refund_amount = order.total_price * Decimal('0.75')
    refund_amount = refund_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)  # Round to 2 decimal places
    
    context = {
        'order': order,
        'refund_amount': refund_amount,
    }
    
    return render(request, 'cancel_ticket_confirmation.html', context)

@login_required
def confirm_cancel_ticket(request, order_id):
    """
    Process the actual ticket cancellation after confirmation
    """
    if request.method != 'POST':
        return redirect('schedule')
    
    # Get the ticket order
    try:
        # Check if user is authenticated through Django auth
        if request.user.is_authenticated:
            order = get_object_or_404(TicketOrder, id=order_id, user=request.user)
        # Check if user is authenticated through session
        elif 'user_id' in request.session:
            user = Users.objects.get(id=request.session['user_id'])
            order = get_object_or_404(TicketOrder, id=order_id, user=user)
        else:
            messages.error(request, 'You must be logged in to cancel tickets.')
            return redirect('schedule')
    except TicketOrder.DoesNotExist:
        messages.error(request, 'Ticket order not found.')
        return redirect('schedule')
    
    # Check if the order is already cancelled
    if order.status == 'Cancelled':
        messages.error(request, 'This ticket has already been cancelled.')
        return redirect('schedule')
    
    # Calculate refund amount (75% of total price)
    refund_amount = order.total_price * Decimal('0.75')
    refund_amount = refund_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)  # Round to 2 decimal places
    
    # Update order status
    order.status = 'Cancelled'
    order.save()
    
    # Free up the seats by marking ticket items as available
    tickets = order.tickets.all()
    for ticket in tickets:
        # Mark the ticket as available
        ticket.is_available = True
        ticket.save()
    
    # If there's a payment record, mark it as refunded
    try:
        payment = TicketPayment.objects.get(ticket_order=order)
        payment.status = 'Refunded'
        payment.save()
        
        # Here you would typically process the refund through Razorpay
        # For example:
        # razorpay_client.refund.create({
        #     "payment_id": payment.razorpay_payment_id,
        #     "amount": int(refund_amount * 100),  # Amount in paise
        #     "notes": {
        #         "order_id": order.order_number,
        #         "reason": "Customer requested cancellation"
        #     }
        # })
        
    except TicketPayment.DoesNotExist:
        # No payment record found, just log it
        print(f"No payment record found for order {order.order_number}")
    
    messages.success(
        request, 
        f'Your ticket has been cancelled successfully. A refund of ₹{refund_amount:.2f} will be processed to your original payment method within 5-7 business days.'
    )
    
    return redirect('schedule')



from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Stand
from django.db import IntegrityError
from django.views.decorators.cache import never_cache

@never_cache
def admin_stadium(request):
    if request.method == 'POST':
        stand_id = request.POST.get('stand_id')
        stand_name = request.POST.get('stand_name', '').strip()
        
        if stand_id:  # This is an update operation
            stand = get_object_or_404(Stand, id=stand_id)
            if stand_name:
                try:
                    stand.name = stand_name
                    stand.save()
                    messages.success(request, 'Stand updated successfully!', extra_tags='admin_edit_stand')
                except IntegrityError:
                    messages.error(request, 'Stand name already exists.', extra_tags='admin_edit_stand')
            else:
                messages.error(request, 'Stand name cannot be empty.', extra_tags='admin_edit_stand')
        else:  # This is an add operation
            if stand_name:
                try:
                    Stand.objects.create(name=stand_name)
                    messages.success(request, 'Stand added successfully!', extra_tags='admin_add_stand')
                except IntegrityError:
                    messages.error(request, 'Stand name already exists.', extra_tags='admin_add_stand')
            else:
                messages.error(request, 'Stand name cannot be empty.', extra_tags='admin_add_stand')
        
        return redirect('admin_stadium')

    # For GET requests, fetch all stands
    stands = Stand.objects.all().order_by('name')
    context = {
        'stands_list': stands
    }
    return render(request, 'admin_stadium.html', context)
    
    
    
from django.contrib import messages

@never_cache
def admin_add_subsection(request):
    if request.method == 'POST':
        section_id = request.POST.get('section_id')
        stand_id = request.POST.get('stand')
        section_name = request.POST.get('section').strip()
        seats_count = request.POST.get('seats')
        price = request.POST.get('price')

        if not stand_id:
            messages.error(request, 'Stand must be selected.', extra_tags='admin_add_section')
        elif not section_name or not section_name.replace(' ', '').isalnum():
            messages.error(request, 'Section name must contain only alphabets, numbers, and spaces.', extra_tags='admin_add_section')
        elif not seats_count or not seats_count.isdigit() or int(seats_count) <= 0:
            messages.error(request, 'Number of seats must be a positive integer.', extra_tags='admin_add_section')
        elif not price or float(price) < 0:
            messages.error(request, 'Price must be a non-negative number.', extra_tags='admin_add_section')
        else:
            try:
                stand = Stand.objects.get(id=stand_id)
                if section_id:  # This is an update operation
                    section = get_object_or_404(Section, id=section_id)
                    if Section.objects.filter(stand=stand, name=section_name).exclude(id=section_id).exists():
                        messages.error(request, 'Section name already exists in the selected stand.', extra_tags='admin_edit_section')
                    else:
                        section.name = section_name
                        section.stand = stand
                        section.seats = list(range(1, int(seats_count) + 1))
                        section.price = float(price)
                        section.save()
                        messages.success(request, 'Section updated successfully!', extra_tags='admin_edit_section success-message')
                else:  # This is an add operation
                    if Section.objects.filter(stand=stand, name=section_name).exists():
                        messages.error(request, 'Section already exists in the selected stand.', extra_tags='admin_add_section')
                    else:
                        seats = list(range(1, int(seats_count) + 1))
                        Section.objects.create(name=section_name, stand=stand, seats=seats, price=float(price))
                        messages.success(request, 'Section added successfully!', extra_tags='admin_add_section success-message')
                return redirect('admin_add_subsection')
            except Stand.DoesNotExist:
                messages.error(request, 'Selected stand does not exist.', extra_tags='admin_add_section')
            except ValueError:
                messages.error(request, 'Invalid price format.', extra_tags='admin_add_section')

    # Fetch all stands and their associated sections
    stands = Stand.objects.all().prefetch_related('sections')

    context = {
        'stand_list': stands,
    }
    return render(request, 'admin_add_subsection.html', context)

@require_POST
def admin_delete_section(request):
    section_id = request.POST.get('section_id')
    try:
        section = Section.objects.get(id=section_id)
        section.delete()
        messages.success(request, 'Section deleted successfully!', extra_tags='admin_delete_section')
        return JsonResponse({'success': True})
    except Section.DoesNotExist:
        messages.error(request, 'Section not found.', extra_tags='admin_delete_section')
        return JsonResponse({'success': False})


def ticket_to_cart(request):
    if request.method == 'POST':
        stand = request.POST.get('stand')
        section = request.POST.get('section')
        seats = int(request.POST.get('seats'))
        ticket_price = float(request.POST.get('ticket_price'))
        
        total_price = seats * ticket_price
        
        # Store the selected tickets and total price in the session
        request.session['cart'] = {
            'stand': stand,
            'section': section,
            'seats': seats,
            'ticket_price': ticket_price,
            'total_price': total_price
        }
        
        return redirect('ticket_checkout')
    return JsonResponse({'error': 'Invalid request'}, status=400)







import logging
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .models import Users, Match

logger = logging.getLogger(__name__)

@require_http_methods(["GET", "POST"])
def ticket_checkout(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'User not logged in'}, status=401)

    user = get_object_or_404(Users, id=user_id)

    if request.method == 'POST':
        # Handle POST request (data coming directly from stadium page)
        match_id = request.POST.get('match_id')
        stand = request.POST.get('stand')
        section = request.POST.get('section')
        quantity = int(request.POST.get('quantity', 1))
        price = float(request.POST.get('price', 0))
    else:
        # Handle GET request (data should be in the session)
        ticket_data = request.session.get('ticket_data', {})
        match_id = ticket_data.get('match_id')
        stand = ticket_data.get('stand')
        section = ticket_data.get('section')
        quantity = int(ticket_data.get('quantity', 1))
        price = float(ticket_data.get('price', 0))

    logger.info(f"Processing ticket checkout for match_id: {match_id}")

    try:
        # Fetch match details using match_id
        match = get_object_or_404(Match, match_id=match_id)
        
        context = {
            'user_email': user.email,  # Use the email from the Users model
            'match_details': {
                'match_id': match.match_id,
                'home_team': match.home_team,
                'away_team': match.away_team,
                'date': match.ist_date.strftime('%d %B %Y'),
                'competition': match.competition,
            },
            'ticket_data': {
                'stand': stand,
                'section': section,
                'quantity': quantity,
                'price': price,
                'total_price': quantity * price,
            },
        }
        return render(request, 'ticket_checkout.html', context)
    except Match.DoesNotExist:
        logger.error(f"Match with match_id {match_id} not found")
        return render(request, 'ticket_checkout.html', {'error': 'Match not found'})







from django.db import transaction
from time import sleep
import random
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import qrcode
from io import BytesIO
import base64
import time
from decimal import Decimal  # Add this import

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import qrcode
from io import BytesIO
import base64
from django.urls import reverse

@csrf_exempt
@require_POST
def allocate_seats(request):
    data = json.loads(request.body)
    match_id = data['matchId']
    stand_name = data['ticketStand']
    section_name = data['ticketSection']
    quantity = int(data['ticketQuantity'])
    full_name = data['fullName']
    email = data['email']
    phone = data['phone']
    total_price = Decimal(data['totalAmount'])

    try:
        with transaction.atomic():
            match = Match.objects.get(match_id=match_id)
            stand = Stand.objects.get(name=stand_name)
            section = Section.objects.get(stand=stand, name=section_name)

            # Get all existing ticket items for this match, stand, and section
            existing_tickets = TicketItem.objects.filter(
                order__match=match,
                stand=stand,
                section=section
            ).select_for_update()  # Lock these rows for update

            # Get all occupied seat numbers
            occupied_seats = set(ticket.seat_number for ticket in existing_tickets if ticket.seat_number is not None)

            # Find available seats
            all_seats = set(range(1, len(section.seats) + 1))
            available_seats = list(all_seats - occupied_seats)
            available_seats.sort()

            if len(available_seats) < quantity:
                return JsonResponse({'success': False, 'error': 'Not enough seats available'})

            assigned_seats = available_seats[:quantity]

            # Get user from session
            user_id = request.session.get('user_id')
            user = Users.objects.get(id=user_id) if user_id else None

            # Create TicketOrder
            order = TicketOrder.objects.create(
                user=user,
                match=match,
                full_name=full_name,
                email=email,
                phone=phone,
                total_price=total_price,
                status='Pending',
                is_paid=False
            )

            # Create TicketItems
            ticket_items = []
            for seat in assigned_seats:
                ticket_item = TicketItem(
                    order=order,
                    stand=stand,
                    section=section,
                    seat_number=seat,
                    price=section.price
                )
                ticket_items.append(ticket_item)

            TicketItem.objects.bulk_create(ticket_items)

            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(f"Order: {order.order_number}, Match: {match.home_team} vs {match.away_team}")
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_image = base64.b64encode(buffer.getvalue()).decode()

            # Prepare email content
            context = {
                'full_name': full_name,
                'match': match,
                'order': order,
                'ticket_items': ticket_items,
                'qr_code': qr_image,
            }
            email_html = render_to_string('email_templates/e_ticket.html', context)

            # Send email
            email = EmailMessage(
                'Your E-Ticket for Real Madrid Match',
                email_html,
                settings.DEFAULT_FROM_EMAIL,
                [email],
            )
            email.content_subtype = "html"
            email.send()

            # Generate URL for booking success page
            success_url = reverse('booking_success', kwargs={'order_number': order.order_number})

            return JsonResponse({
                'success': True, 
                'assigned_seats': assigned_seats,
                'order_number': order.order_number,
                'redirect_url': success_url
            })

    except (Match.DoesNotExist, Stand.DoesNotExist, Section.DoesNotExist) as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Users.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f"An unexpected error occurred: {str(e)}"})




def booking_success(request, order_number):
    # Get the confirmed order
    order = get_object_or_404(TicketOrder, order_number=order_number, status='Confirmed')
    
    # Ensure the order belongs to the current user
    if request.user.is_authenticated:
        if order.user != request.user:
            raise Http404
    elif 'user_id' in request.session:
        if order.user.id != request.session['user_id']:
            raise Http404
    else:
        raise Http404

    # Get ticket items
    ticket_items = order.tickets.all()
    
    # Get match details directly from the order's match
    match = order.match
    
    # Convert match time to IST and format separately for date and time
    ist_timezone = pytz.timezone('Asia/Kolkata')
    match_time = match.utc_date.astimezone(ist_timezone)
    
    match_details = {
        'home_team': match.home_team,
        'away_team': match.away_team,
        'date': match_time.strftime('%B %d, %Y'),
        'time': match_time.strftime('%I:%M %p IST'),
        'venue': match.venue or 'Santiago Bernabéu',
        'competition': match.competition
    }

    # Prepare email content
    context = {
        'order': order,
        'match_details': match_details,
        'ticket_items': ticket_items,
    }
    
    # Render HTML email template
    html_content = render_to_string('email/booking_confirmation.html', context)
    text_content = strip_tags(html_content)  # Plain text version of email
    
    # Create email
    subject = f'Real Madrid FC - Booking Confirmation #{order.order_number}'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = order.email

    # Send email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=[to_email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

    # Return the normal booking success response
    return render(request, 'booking_success.html', context)






def custom_jersey(request):
    categories = Category.objects.all()  # Fetch all categories
    return render(request, 'custom_jersey.html', {'categories': categories})  # Pass categories to the template


    
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.select_related('shipping'), id=order_id)
    return render(request, 'order_detail.html', {'order': order})

def match_details(request):
    return render(request,'match_details.html')


def admin_view_orders(request):
    # Get all orders and order them by creation date (newest first)
    all_orders = Order.objects.all().order_by('-created_at')
    
    # Set up pagination
    page = request.GET.get('page', 1)
    items_per_page = 20  # You can adjust this number
    paginator = Paginator(all_orders, items_per_page)
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    
    # Prepare order data for the template
    order_data = []
    for order in orders:
        order_items = OrderItem.objects.filter(order=order)
        total_quantity = sum(item.quantity for item in order_items)
        order_data.append({
            'order': order,
            'items': order_items,
            'total_quantity': total_quantity,
        })
    
    context = {
        'order_data': order_data,
        'orders': orders,  # This is for pagination
    }
    
    return render(request, 'admin_view_orders.html', context)




def view_order(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Please log in to view your orders.")
        return redirect('login')  # Redirect to login page if user is not logged in

    try:
        user = Users.objects.get(id=user_id)
        orders = Order.objects.filter(user=user).order_by('-created_at')
        
        # Debugging information
        debug_info = f"User: {user.username}, User ID: {user_id}, Order count: {orders.count()}"
        print(debug_info)  # This will print to the console
        
        if not orders:
            # If no orders, let's check if there are any orders at all
            all_orders = Order.objects.all()
            print(f"Total orders in database: {all_orders.count()}")
            if all_orders:
                print("Sample order:", all_orders.first())
        
        return render(request, 'view_order.html', {'orders': orders, 'debug_info': debug_info})
    
    except Users.DoesNotExist:
        messages.error(request, "User not found. Please try logging in again.")
        return redirect('login')


def checkout(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Please log in to proceed with checkout.")
        return redirect('login')

    user = Users.objects.get(id=user_id)
    cart = Cart.objects.get(user=user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('item')

    # Fetch the last order's address for the user
    last_order = Order.objects.filter(user=user).order_by('-created_at').first()
    last_address = {
        'full_name': last_order.full_name if last_order else '',
        'phone': last_order.phone if last_order else '',
        'email': last_order.email if last_order else '',  # Add email here
        'address': last_order.address if last_order else '',
        'apartment': last_order.apartment if last_order else '',
        'country': last_order.country if last_order else '',
        'state': last_order.state if last_order else '',
        'city': last_order.city if last_order else '',
        'zipcode': last_order.zipcode if last_order else '',
    }

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        
        details = data.get('details', {})
        shipping_method = data.get('shippingMethod')
        payment_response = data.get('payment_response', {})

        logger.info(f"Received checkout data: {data}")

        if payment_response.get('success'):
            try:
                with transaction.atomic():
                    # Create Order
                    order = Order.objects.create(
                        user=user,
                        full_name=details.get('fullname', last_address['full_name']),
                        email=details.get('email'),
                        phone=details.get('phone', last_address['phone']),
                        address=details.get('address', last_address['address']),
                        apartment=details.get('apartment', last_address['apartment']),
                        country=details.get('country', last_address['country']),
                        state=details.get('state', last_address['state']),
                        city=details.get('city', last_address['city']),
                        zipcode=details.get('zipcode', last_address['zipcode']),
                        total=sum(item.item.price * item.quantity for item in cart_items),
                        status='Processing',
                        is_paid=True
                    )
                    logger.info(f"Created order: {order.order_number}")

                    # Create OrderItems
                    for cart_item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            item=cart_item.item,
                            quantity=cart_item.quantity,
                            price=cart_item.item.price,
                            size=cart_item.size
                        )
                        logger.info(f"Created order item for: {cart_item.item.name}")

                        # Update inventory
                        item_size = ItemSize.objects.filter(item=cart_item.item, size=cart_item.size).first()
                        if item_size:
                            if item_size.quantity < cart_item.quantity:
                                raise ValueError(f"Not enough stock for {cart_item.item.name}")
                            item_size.quantity -= cart_item.quantity
                            item_size.save()
                            logger.info(f"Updated inventory for: {cart_item.item.name}, size: {cart_item.size}")

                    # Create Payment
                    payment = Payment.objects.create(
                        order=order,
                        payment_method='Razorpay',
                        transaction_id=payment_response.get('payment_id'),
                        amount_paid=order.total,
                        status='Completed'
                    )
                    logger.info(f"Created payment: {payment.transaction_id}")

                    # Create Shipping
                    shipping_cost = 5.00 if shipping_method == 'standard' else 15.00
                    shipping = Shipping.objects.create(
                        order=order,
                        shipping_method=shipping_method,
                        shipping_cost=shipping_cost,
                        status='Pending',
                        estimated_delivery=timezone.now().date() + timezone.timedelta(days=7)
                    )
                    logger.info(f"Created shipping for order: {order.order_number}")

                    # Clear the cart
                    cart.items.all().delete()
                    logger.info(f"Cleared cart for user: {user.id}")

                    return JsonResponse({'success': True, 'order_number': order.order_number, 'redirect': '/payment_success/'})

            except ValueError as e:
                logger.error(f"ValueError in checkout: {str(e)}")
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            except Exception as e:
                logger.error(f"Unexpected error in checkout: {str(e)}", exc_info=True)
                return JsonResponse({'success': False, 'error': 'An unexpected error occurred'}, status=500)
        else:
            logger.warning("Payment was not successful")
            return JsonResponse({'success': False, 'error': 'Payment was not successful'}, status=400)

    else:  # GET request
        context = {
            'cart_items': [
                {
                    'id': item.item.id,
                    'name': item.item.name,
                    'quantity': item.quantity,
                    'size': item.size,
                    'price': float(item.item.price),
                    'total': float(item.item.price * item.quantity),
                    'image': item.item.main_image.url if item.item.main_image else '',
                }
                for item in cart_items
            ],
             'last_address': last_address if any(last_address.values()) else None,  # Pass the last address only if it contains values
        }
        return render(request, 'checkout.html', context)



def real_madrid_fixtures(request):
    api_key = 'dc93cd61f7a04a67be5652fc72195459'
    url = 'https://api.football-data.org/v4/teams/86/matches'  # Real Madrid's ID is 86
    headers = {'X-Auth-Token': api_key}

    response = requests.get(url, headers=headers)
    fixtures = response.json().get('matches', [])

    return render(request, 'index.html', {'fixtures': fixtures})





@csrf_protect
@require_POST
def remove_from_cart(request):
    user_id = request.session.get('user_id')
    if not user_id:
        logger.error(f"User not authenticated. Session: {request.session.items()}")
        return JsonResponse({'error': 'User not authenticated'}, status=401)

    try:
        data = json.loads(request.body)
        cart_item_id = data.get('item_id')  # This is actually the CartItem.id
        logger.info(f"Removing item. User ID: {user_id}, CartItem ID: {cart_item_id}")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON. Request body: {request.body}")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not cart_item_id:
        logger.error(f"Invalid request. CartItem ID: {cart_item_id}")
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        user = Users.objects.get(id=user_id)
        cart = Cart.objects.get(user=user)
        cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
        logger.info(f"Found cart item. Cart ID: {cart.id}, CartItem ID: {cart_item_id}")
        cart_item.delete()
        return JsonResponse({'success': True, 'message': 'Item removed from cart'})
    except Users.DoesNotExist:
        logger.error(f"User not found. User ID: {user_id}")
    except Cart.DoesNotExist:
        logger.error(f"Cart not found. User ID: {user_id}")
    except CartItem.DoesNotExist:
        logger.error(f"CartItem not found. User ID: {user_id}, CartItem ID: {cart_item_id}")
    
    return JsonResponse({'error': 'Item not found in cart'}, status=404)


def add_to_wishlist(request):
    if request.method == 'POST':
        # Get the user using session ID
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, "Please log in to add items to wishlist.", extra_tags='specific_login_required')
            # Redirect to the same page without accessing item details
            return redirect(request.META.get('HTTP_REFERER', 'store'))

        item_id = request.POST.get('item_id')
        
        user = get_object_or_404(Users, id=user_id)
        item = get_object_or_404(Item, id=item_id)
        
        # Get or create wishlist for the user
        wishlist, _ = Wishlist.objects.get_or_create(user=user)
        
        # Try to create a new wishlist item
        _, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            item=item
        )
        
        if created:
            messages.success(request, f"{item.name} added to your wishlist.", extra_tags='add_to_wishlist_success')
        else:
            messages.info(request, f"{item.name} is already in your wishlist.", extra_tags='add_to_wishlist_info')
        
        return redirect('product_single_view', category_id=item.category.id, item_id=item.id)
    
    return redirect('store')  # Redirect to store if not a POST request


from django.db.models import Prefetch,F

def view_wishlist(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')  # Redirect to login if user is not authenticated

    user = Users.objects.get(id=user_id)
    wishlist, created = Wishlist.objects.get_or_create(user=user)
    
    # Fetch wishlist items with related item data
    wishlist_items = WishlistItem.objects.filter(wishlist=wishlist).select_related('item', 'item__category').prefetch_related(
        'item__additional_images'
    )

    # Prepare wishlist items with image URLs
    wishlist_items_with_images = []
    for wishlist_item in wishlist_items:
        item = wishlist_item.item
        image_url = item.main_image.url if item.main_image else None
        if not image_url:
            additional_images = item.additional_images.all()
            if additional_images:
                image_url = additional_images[0].image.url

        wishlist_items_with_images.append({
            'wishlist_item': wishlist_item,
            'image_url': image_url
        })

    # Calculate total value
    total_value = sum(item.item.price for item in wishlist_items)

    context = {
        'wishlist_items': wishlist_items_with_images,
        'total_value': total_value,
    }
    return render(request, 'wishlist.html', context)



@require_POST
def remove_from_wishlist(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Please log in to manage your wishlist.")
        return redirect('login')

    wishlist_item_id = request.POST.get('wishlist_item_id')
    if not wishlist_item_id:
        messages.error(request, "Invalid request. Item not specified.")
        return redirect('view_wishlist')

    try:
        user = get_object_or_404(Users, id=user_id)
        wishlist_item = get_object_or_404(WishlistItem, id=wishlist_item_id, wishlist__user=user)
        item_name = wishlist_item.item.name
        wishlist_item.delete()
        messages.success(request, f"{item_name} has been removed from your wishlist.")
    except WishlistItem.DoesNotExist:
        messages.error(request, "Item not found in your wishlist.")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")

    return redirect('view_wishlist')




def add_to_cart(request):
    if request.method == 'POST':
        # Get the user using session ID
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, "Please log in to add items to cart.", extra_tags='specific_login_required')
            # Redirect to the same page without accessing item details
            return redirect(request.META.get('HTTP_REFERER', 'store'))

        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        size = request.POST.get('size')
        
        user = get_object_or_404(Users, id=user_id)
        item = get_object_or_404(Item, id=item_id)
        
        # Get or create cart for the user
        cart, created = Cart.objects.get_or_create(user=user)
        
        # Check if item already in cart
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            item=item,
            size=size
        )
        
        if not item_created:
            cart_item.quantity += quantity
            cart_item.save()
        else:
            cart_item.quantity = quantity
            cart_item.save()
        
        messages.success(request, f"{item.name} added to your cart.", extra_tags='add_to_cart_success')
        return redirect('product_single_view', category_id=item.category.id, item_id=item.id)
    
    return redirect('store')  # Redirect to store if not a POST request










@csrf_protect
@require_POST
def update_cart_quantity(request):
    user_id = request.session.get('user_id')
    if not user_id:
        logger.error(f"User not authenticated. Session: {request.session.items()}")
        return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)

    try:
        data = json.loads(request.body)
        cart_item_id = data.get('item_id')
        quantity_change = data.get('quantity_change')
        logger.info(f"Updating item quantity. User ID: {user_id}, CartItem ID: {cart_item_id}, Change: {quantity_change}")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON. Request body: {request.body}")
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    if not cart_item_id or quantity_change is None:
        logger.error(f"Invalid request. CartItem ID: {cart_item_id}, Quantity change: {quantity_change}")
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

    try:
        user = Users.objects.get(id=user_id)
        cart = Cart.objects.get(user=user)
        cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
        
        new_quantity = cart_item.quantity + quantity_change
        available_quantity = cart_item.get_available_quantity()
        
        if new_quantity <= 0:
            logger.info(f"Removing item from cart. Cart ID: {cart.id}, CartItem ID: {cart_item_id}")
            cart_item.delete()
            return JsonResponse({'success': True, 'message': 'Item removed from cart'})
        
        if new_quantity > available_quantity:
            logger.error(f"Requested quantity exceeds available stock. CartItem ID: {cart_item_id}")
            return JsonResponse({
                'success': False, 
                'error': 'Not enough stock available',
                'available_quantity': available_quantity
            }, status=400)
        
        cart_item.quantity = new_quantity
        cart_item.save()
        
        logger.info(f"Updated cart item quantity. Cart ID: {cart.id}, CartItem ID: {cart_item_id}, New quantity: {new_quantity}")
        return JsonResponse({
            'success': True, 
            'message': 'Cart updated successfully', 
            'new_quantity': new_quantity,
            'available_quantity': available_quantity
        })
    except Users.DoesNotExist:
        logger.error(f"User not found. User ID: {user_id}")
    except Cart.DoesNotExist:
        logger.error(f"Cart not found. User ID: {user_id}")
    except CartItem.DoesNotExist:
        logger.error(f"CartItem not found. User ID: {user_id}, CartItem ID: {cart_item_id}")
    except Item.DoesNotExist:
        logger.error(f"Item not found. CartItem ID: {cart_item_id}")
    
    return JsonResponse({'success': False, 'error': 'Failed to update cart'}, status=404)


def add_position(request):
    if request.method == 'POST':
        position_name = request.POST.get('position')
        if position_name:
            Position.objects.create(position=position_name)
            messages.success(request, 'Position added successfully!')
            return redirect('admin_add_player')  # Redirect to the page where you want to show the message
    return render(request, 'admin_add_player.html')

def add_news(request):
    if request.method == 'POST':
        title = request.POST.get('title').strip()
        description = request.POST.get('description').strip()
        news_image = request.FILES.get('news_image')

        # Create a new News object
        news = News(
            title=title,
            description=description,
        )

        if news_image:
            news.news_image = news_image

        # Save the news to the database
        news.save()

        # Add a success message
        messages.success(request, 'News added successfully!')

        # Render the same page again with a success message
        return render(request, 'admin_add_news.html')

    return render(request, 'admin_add_news.html')

def add_player(request):
    if request.method == 'POST':
        jersey_num = request.POST.get('jersey_num').strip()
        player_name = request.POST.get('player_name').strip()
        player_country = request.POST.get('player_country').strip()
        player_position = request.POST.get('player_position')
        player_role = request.POST.get('player_role').strip()
        player_image = request.FILES.get('player_image')

        # Remove validation logic as it's handled on the front end

        # Save the player to the database
        player = Player(
            jersey_num=jersey_num,
            player_name=player_name,
            player_country=player_country,
            player_position_id=player_position,  # Assuming position is the ID of the related Position object
            player_role=player_role,
        )

        if player_image:
            player.player_image = player_image

        player.save()

        # Add a success message
        messages.success(request, 'Player added successfully!', extra_tags='add_player')
        return redirect('admin_add_player')  # Redirect to the page where you want to show the message

    return render(request, 'add_player.html')

def admin_add_item(request):
    if request.method == 'POST':
        with transaction.atomic():
            try:
                # Create the main Item
                item = Item.objects.create(
                    category_id=request.POST.get('category'),
                    subcategory_id=request.POST.get('subcategory'),
                    name=request.POST.get('name'),
                    price=request.POST.get('price'),
                    description=request.POST.get('description'),
                    main_image=request.FILES.get('main_image')
                )

                # Handle sizes and quantities
                sizes = request.POST.getlist('sizes[]')
                quantities = request.POST.getlist('quantities[]')
                for size, quantity in zip(sizes, quantities):
                    if  quantity:
                        ItemSize.objects.create(
                            item=item,
                            size=size or None,
                            quantity=int(quantity)
                        )

                # Handle additional images
                for image in request.FILES.getlist('additional_images'):
                    ItemImage.objects.create(item=item, image=image)

                messages.success(request, 'Item added successfully!')
                return redirect('admin_add_item')

            except Exception as e:
                messages.error(request, f'Error adding item: {str(e)}')

    # GET request handling remains the same
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'admin_add_item.html', context)


def get_subcategories(request, category_id):
    subcategories = SubCategory.objects.filter(category_id=category_id).values('id', 'sub_category_name')
    return JsonResponse(list(subcategories), safe=False)



def admin_update_player(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    position_list = Position.objects.all()

    if request.method == 'POST':
        player.jersey_num = request.POST.get('jersey_num')
        player.player_name = request.POST.get('player_name')
        player.player_country = request.POST.get('player_country')
        player.player_position_id = request.POST.get('player_position')
        player.player_role = request.POST.get('player_role')

        if 'player_image' in request.FILES:
            player.player_image = request.FILES['player_image']
        
        player.save()
        messages.success(request, 'Player information updated successfully.')
        return redirect('admin_squad_list')  # Redirect to admin_squad_list page after update

    context = {
        'player': player,
        'position_list': position_list,
    }
    return render(request, 'admin_update_player.html', context)



from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch

def generate_report(request, order_id):
    order = Order.objects.get(id=order_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="order_{order_id}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)

    # Set up some margins
    left_margin = 50
    right_margin = 550
    top_margin = 750
    bottom_margin = 50

    # Add a logo or placeholder (optional)
    p.setFont("Helvetica-Bold", 24)
    p.drawString(left_margin, top_margin, "Real Madrid Store")  # Placeholder for the logo
    p.setFont("Helvetica", 16)
    p.drawString(left_margin, top_margin - 30, "Invoice")

    # Invoice information box
    p.setFont("Helvetica", 12)
    p.setLineWidth(0.5)
    p.rect(left_margin, top_margin - 80, 500, 60, stroke=1, fill=0)
    p.drawString(left_margin + 10, top_margin - 60, f"Order Number: {order.order_number}")
    p.drawString(left_margin + 10, top_margin - 75, f"Order Date: {order.created_at.strftime('%d %B %Y')}")
    p.drawString(right_margin - 200, top_margin - 60, f"Customer Name: {order.full_name}")
    p.drawString(right_margin - 200, top_margin - 75, f"Email: {order.email}")

    # Add a line break
    p.line(left_margin, top_margin - 90, right_margin, top_margin - 90)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(left_margin, top_margin - 110, "Billing Information")
    p.setFont("Helvetica", 12)
    p.drawString(left_margin, top_margin - 130, f"Phone: {order.phone}")
    p.drawString(left_margin, top_margin - 150, "Shipping Address:")

    # Table headers with background color and better spacing
    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.lightgrey)
    p.rect(left_margin, top_margin - 190, 500, 20, fill=1)  # Background for the header row
    p.setFillColor(colors.black)
    p.drawString(left_margin + 10, top_margin - 185, "Item")
    p.drawString(left_margin + 250, top_margin - 185, "Quantity")
    p.drawString(left_margin + 350, top_margin - 185, "Price (€)")
    p.drawString(left_margin + 450, top_margin - 185, "Total (€)")

    # Add items to the bill with alternating row colors
    y_position = top_margin - 210
    row_alternate = False
    max_item_width = 230

    def wrap_text(text, max_width, canvas):
        """Helper function to wrap text into multiple lines if it exceeds the max width."""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if canvas.stringWidth(test_line, "Helvetica", 12) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)  # Append the last line
        return lines

    for item in order.items.all():
        if row_alternate:
            p.setFillColor(colors.whitesmoke)  # Alternating row color
            p.rect(left_margin, y_position, 500, 20, fill=1)
        else:
            p.setFillColor(colors.white)
        row_alternate = not row_alternate

        p.setFillColor(colors.black)
        p.setFont("Helvetica", 12)
        
        # Wrap the item name if necessary
        item_lines = wrap_text(item.item.name, max_item_width, p)

        for line in item_lines:
            p.drawString(left_margin + 10, y_position + 5, line)
            y_position -= 15
        
        p.drawString(left_margin + 260, y_position + 15, str(item.quantity))
        p.drawString(left_margin + 360, y_position + 15, f"{item.price:.2f}")
        p.drawString(left_margin + 460, y_position + 15, f"{item.price * item.quantity:.2f}")
        
        y_position -= 5  # Adjust for line height
    
    # Total Amount
    p.setLineWidth(1)
    p.line(left_margin, y_position - 10, right_margin, y_position - 10)
    y_position -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(left_margin + 350, y_position, "Total Amount:")
    p.drawString(left_margin + 460, y_position, f"€{order.total:.2f}")

    # Footer with some info
    p.setFont("Helvetica", 10)
    p.drawString(left_margin, y_position - 40, "Thank you for your purchase!")
    p.drawString(left_margin, y_position - 55, "For any inquiries, contact us at support@yourwebsite.com")
    p.drawString(left_margin, y_position - 70, "Your Company Name | Your Address | Your Contact Info")

    # Draw a border around the invoice
    p.setLineWidth(1)
    p.rect(left_margin, bottom_margin, 500, top_margin - 150, stroke=1, fill=0)

    # Finalize the page
    p.showPage()
    p.save()

    return response








from django.shortcuts import render, get_object_or_404
from .models import Match, TicketItem, Stand, Section  # Ensure Stand and Section are imported
from django.utils import timezone
from django.db.models import Count  # Add this import for aggregation

def admin_ticket_stats(request):
    # Fetch only home matches for Real Madrid
    matches = Match.objects.filter(home_team='Real Madrid CF', utc_date__gt=timezone.now())
    selected_match = None
    tickets_sold = 0
    total_seats = 0
    stand_booking_data = {}  # Dictionary to hold booking data for stands

    if request.method == 'POST':
        match_id = request.POST.get('match_id')
        selected_match = get_object_or_404(Match, match_id=match_id)

        # Calculate total seats available for the selected match
        total_seats = 0
        for stand in Stand.objects.all():
            sections = Section.objects.filter(stand=stand)
            for section in sections:
                total_seats += len(section.seats)  # Assuming seats are stored as a list in JSONField

            # Calculate tickets sold for the selected match and aggregate by stand
            tickets_sold_for_stand = TicketItem.objects.filter(order__match=selected_match, stand=stand).count()
            stand_booking_data[stand.name] = tickets_sold_for_stand  # Store tickets sold for each stand

        # Calculate tickets sold for the selected match
        tickets_sold = TicketItem.objects.filter(order__match=selected_match).count()

    tickets_available = total_seats - tickets_sold

    # Prepare data for graph (e.g., bar chart)
    stand_names = list(stand_booking_data.keys())
    tickets_sold_counts = list(stand_booking_data.values())

    context = {
        'matches': matches,
        'selected_match': selected_match,
        'tickets_sold': tickets_sold,
        'total_seats': total_seats,
        'tickets_available': tickets_available,
        'stand_names': stand_names,  # Pass stand names for graph
        'tickets_sold_counts': tickets_sold_counts,  # Pass ticket counts for graph
    }
    return render(request, 'admin_ticket_stats.html', context)



from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.shortcuts import render

from .models import TicketItem, Match, TicketOrder, Section, Stand  # Ensure these models are imported

@never_cache
def admin_dashboard(request):
    # Date range for charts (last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Get total sales (all time)
    total_sales = Order.objects.aggregate(total=Sum('total'))['total'] or 0

    # Get total revenue (all time)
    revenue = Payment.objects.filter(status='Completed').aggregate(total=Sum('amount_paid'))['total'] or 0

    # New Customers (last 30 days)
    new_customers = Users.objects.filter(date_joined__gte=start_date).count()

    # Top Selling Products (by quantity)
    top_products = Item.objects.annotate(
        total_quantity=Sum('orderitem__quantity')
    ).order_by('-total_quantity')[:5]

    # Prepare data for product sales comparison chart (number of items sold)
    product_names = [product.name for product in top_products]
    product_sales_data = [product.total_quantity for product in top_products]

    # Fetch upcoming matches
    upcoming_matches = Match.objects.filter(utc_date__gt=timezone.now()).order_by('utc_date')

    # Prepare data for tickets sold and available for each upcoming match
    match_ticket_data = []
    for match in upcoming_matches:
        tickets_sold = TicketItem.objects.filter(order__match=match).count()

        # Calculate total tickets from all sections related to the venue of the match
        total_tickets = 0
        stands = Stand.objects.filter(name=match.venue)  # Assuming the venue name matches the stand name
        for stand in stands:
            sections = Section.objects.filter(stand=stand)
            for section in sections:
                total_tickets += len(section.seats)  # Assuming seats are stored as a JSON list

        tickets_available = total_tickets - tickets_sold

        match_ticket_data.append({
            'match_id': match.match_id,
            'home_team': match.home_team,
            'away_team': match.away_team,
            'tickets_sold': tickets_sold,
            'tickets_available': tickets_available,
        })

    # Prepare data for the pie chart
    pie_chart_data = []
    for match in match_ticket_data:
        pie_chart_data.append({
            'match': f"{match['home_team']} vs {match['away_team']}",
            'sold': match['tickets_sold'],
            'available': match['tickets_available'],
        })

    # Context to pass to the template
    context = {
        'total_sales': total_sales,
        'revenue': revenue,
        'new_customers': new_customers,
        'top_products': top_products,
        'product_names': product_names,
        'product_sales_data': product_sales_data,
        'match_ticket_data': match_ticket_data,
        'upcoming_matches': upcoming_matches,
        'pie_chart_data': pie_chart_data,  # Add pie chart data to context
    }

    if request.user.is_authenticated:
        user = request.user
        context.update({
            'user_name': user.username,
            'user_email': user.email,
            'user_phone': getattr(user, 'phone', None),  # Optional: if you have a phone field in the User model
        })
    elif 'user_id' in request.session:
        try:
            user = Users.objects.get(id=request.session['user_id'])
            context.update({
                'user_name': user.name,
                'user_email': user.email,
                'user_phone': user.phone,  # Add other user-specific details if needed
            })
        except Users.DoesNotExist:
            pass

    return render(request, 'admin_dashboard.html', context)


def admin_add_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('category').strip()  # Strip leading/trailing whitespace
        if category_name and all(char.isalpha() or char.isspace() for char in category_name):
            if Category.objects.filter(category_name=category_name).exists():
                messages.error(request, 'Category already exists.', extra_tags='admin_add_category')
            else:
                Category.objects.create(category_name=category_name)
                messages.success(request, 'Category added successfully!', extra_tags='admin_add_category')
            return redirect('admin_add_category')
        else:
            messages.error(request, 'Category must contain only alphabets and spaces, and cannot be empty', extra_tags='admin_add_category')

    # Fetch all categories from the database
    categories = Category.objects.all()

    return render(request, 'admin_add_category.html', {'category_list': categories})


def admin_add_subcategory(request):
    if request.method == 'POST':
        category_id = request.POST.get('category')
        sub_category_name = request.POST.get('subcategory').strip()

        if not category_id:
            messages.error(request, 'Product category must be selected.', extra_tags='admin_add_subcategory')
        elif not sub_category_name or not all(char.isalpha() or char.isspace() for char in sub_category_name):
            messages.error(request, 'Subcategory must contain only alphabets and cannot be empty.', extra_tags='admin_add_subcategory')
        else:
            # Check if the subcategory already exists in the selected category
            if SubCategory.objects.filter(sub_category_name=sub_category_name, category_id=category_id).exists():
                messages.error(request, 'Subcategory already exists in the selected category.', extra_tags='admin_add_subcategory')
            else:
                # Create the new subcategory
                SubCategory.objects.create(sub_category_name=sub_category_name, category_id=category_id)
                messages.success(request, 'Subcategory added successfully!', extra_tags='admin_add_subcategory')
                return redirect('admin_add_subcategory')  # Redirect to the same page to show the success message

    # Fetch all categories and their associated subcategories
    categories = Category.objects.all().prefetch_related('subcategory_set')

    return render(request, 'admin_add_subcategory.html', {'category_list': categories})


from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .models import Player, Position, SeasonStats  # Added SeasonStats import
import logging
logger = logging.getLogger(__name__)

@csrf_exempt
def admin_add_player(request):
    if request.method == 'POST':
        try:
            # Helper function to convert to Decimal or None
            def to_decimal(value):
                if not value or value == '':
                    return None
                try:
                    # Replace comma with dot if present and strip any spaces
                    cleaned_value = str(value).replace(',', '.').strip()
                    return Decimal(cleaned_value)
                except (InvalidOperation, ValueError):
                    logger.error(f"Invalid decimal value: {value}")
                    return None

            # Log the incoming data for debugging
            logger.info(f"Height value received: {request.POST.get('height')}")
            logger.info(f"Weight value received: {request.POST.get('weight')}")

            # Convert height and weight first
            height = to_decimal(request.POST.get('height'))
            weight = to_decimal(request.POST.get('weight'))

            # Create new player object
            player = Player(
                jersey_num=request.POST.get('jersey_num'),
                player_name=request.POST.get('player_name'),
                player_country=request.POST.get('player_country'),
                player_position=Position.objects.get(id=request.POST.get('player_position')),
                player_role=request.POST.get('player_role'),
                date_of_birth=request.POST.get('date_of_birth') or None,
                height=height,
                weight=weight,
                appearances=int(request.POST.get('appearances') or 0),
                goals=int(request.POST.get('goals') or 0),
                assists=int(request.POST.get('assists') or 0),
                clean_sheets=int(request.POST.get('clean_sheets') or 0),
                yellow_cards=int(request.POST.get('yellow_cards') or 0),
                red_cards=int(request.POST.get('red_cards') or 0),
                biography=request.POST.get('biography', ''),
                joined_date=request.POST.get('joined_date') or None,
                contract_end_date=request.POST.get('contract_end_date') or None,
            )

            if 'player_image' in request.FILES:
                player.player_image = request.FILES['player_image']

            player.save()

            # Create season stats if provided
            season = request.POST.get('season')
            competition = request.POST.get('competition')
            if season and competition:
                SeasonStats.objects.create(
                    player=player,
                    season=season,
                    competition=competition,
                    appearances=int(request.POST.get('appearances') or 0),
                    goals=int(request.POST.get('goals') or 0),
                    assists=int(request.POST.get('assists') or 0),
                    minutes_played=int(request.POST.get('minutes_played') or 0)
                )
            
            # Handle achievements
            achievements = json.loads(request.POST.get('achievements', '[]'))
            for achievement in achievements:
                PlayerAchievement.objects.create(
                    player=player,  # player object from your existing code
                    title=achievement['title'],
                    description=achievement['description'],
                    date=achievement['date'] if achievement['date'] else None
                )

            return JsonResponse({'success': True})
        except InvalidOperation as e:
            logger.error(f"Invalid decimal operation: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': f'Please enter valid numbers for height and weight: {str(e)}'
            })
        except ValueError as e:
            logger.error(f"Value error: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': f'Invalid number format: {str(e)}'
            })
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': f'Validation error: {str(e)}'
            })
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': f'An unexpected error occurred: {str(e)}'
            })
    
    # For GET requests, render the template
    positions = Position.objects.all()
    return render(request, 'admin_add_player.html', {'positions': positions})





def admin_view_store(request):
    # Fetch all categories
    categories = Category.objects.all()
    
    # Initialize an empty dictionary to hold category-wise items
    category_items = {}

    for category in categories:
        # Fetch items related to the category
        items = Item.objects.filter(category=category)

        # Organize items by their subcategory
        subcategory_items = {}
        for item in items:
            subcategory = item.subcategory if item.subcategory else 'No subcategory'
            if subcategory not in subcategory_items:
                subcategory_items[subcategory] = []
            subcategory_items[subcategory].append(item)

        category_items[category] = subcategory_items

    return render(request, 'admin_view_store.html', {'category_items': category_items})










@never_cache
def admin_squad_list(request):
    # Fetch all positions
    positions = Position.objects.all()

    # Create a dictionary to hold players by position
    players_by_position = {}
    for position in positions:
        players_by_position[position.position] = Player.objects.filter(player_position=position)

    return render(request, 'admin_squad_list.html', {'players_by_position': players_by_position})




def store(request):
    # Fetch all categories
    categories = Category.objects.all()

  

    # Get the current category from the request, default to the first category if none specified
    current_category_id = request.GET.get('category')
    if current_category_id:
        current_category = get_object_or_404(Category, id=current_category_id)
    else:
        current_category = categories.first()  # Set to the first category if none is selected

    # Get the index of the current category to find the next category
    current_index = list(categories).index(current_category) if current_category else 0
    next_category = categories[current_index + 1] if current_index + 1 < len(categories) else None

    # Fetch subcategories for the current category
    subcategories = SubCategory.objects.filter(category=current_category) if current_category else []

    # Get the selected subcategory from the request
    selected_subcategory_id = request.GET.get('subcategory')

    # Initialize items queryset
    items = Item.objects.all()

   
    if current_category:
        # If only a category is selected, filter items based on the category
        items = items.filter(category=current_category)

    # Limit to 3 items for display
    items = items[:3]

    # Fetch items for the next category
    next_category_items = Item.objects.filter(category=next_category)[:3] if next_category else []

    # Prepare data for all categories with the first 3 items
    all_category_items = {}
    for category in categories:
        # Fetch the first 3 items for each category (without ordering)
        three_items = Item.objects.filter(category=category)[:3]
        all_category_items[category] = three_items

    context = {
        'categories': categories,
        'current_category': current_category,
        'next_category': next_category,
        'subcategories': subcategories,
        'items': items,
        'next_category_items': next_category_items,
        'selected_subcategory_id': selected_subcategory_id,
        'all_category_items': all_category_items,
    }

    return render(request, 'store.html', context)



from django.http import JsonResponse
from .models import Item

def search_products(request):
    query = request.GET.get('query', '')
    if query:
        items = Item.objects.filter(name__icontains=query)[:10]  # Limit to 10 results
        results = [{
            'id': item.id,
            'name': item.name,
            'price': item.price,
            'main_image': item.main_image.url if item.main_image else '',
            'category_id': item.category.id,  # Include category_id
        } for item in items]
        return JsonResponse(results, safe=False)
    return JsonResponse([], safe=False)

def wishlist(request):
    return render(request, 'wishlist.html')





def admin_edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    categories = Category.objects.all()
    subcategories = SubCategory.objects.filter(category=item.category)  # Filter subcategories based on the item's category

    # Fetch sizes and quantities
    item.sizes_quantity_pairs = item.get_sizes_and_quantities()

    if request.method == 'POST':
        item.name = request.POST.get('name')
        item.category_id = request.POST.get('category')
        item.subcategory_id = request.POST.get('subcategory')
        item.price = request.POST.get('price')
        item.description = request.POST.get('description')

        if 'main_image' in request.FILES:
            item.main_image = request.FILES['main_image']
        
        item.save()

        # Handling additional images
        if 'additional_images' in request.FILES:
            for image in request.FILES.getlist('additional_images'):
                ItemImage.objects.create(item=item, image=image)

        # Handling sizes and quantities
        sizes = request.POST.getlist('sizes[]')
        quantities = request.POST.getlist('quantities[]')

        ItemSize.objects.filter(item=item).delete()  # Remove existing sizes
        for size, quantity in zip(sizes, quantities):
            if size:
                ItemSize.objects.create(item=item, size=size, quantity=quantity)

        messages.success(request, 'Item updated successfully.')
        return redirect('admin_view_store')

    return render(request, 'admin_edit_item.html', {
        'item': item,
        'categories': categories,
        'subcategories': subcategories
    })

  


def product_single_view(request, category_id, item_id):
    
    categories = Category.objects.all()

    category = get_object_or_404(Category, id=category_id)
    item = get_object_or_404(Item, id=item_id, category=category)
    
    # Get sizes with quantity > 0
    sizes_with_stock = item.sizes.filter(quantity__gt=0)
    
    # Calculate total quantity
    total_quantity = sizes_with_stock.aggregate(total=Sum('quantity'))['total'] or 0

    # Get related items (adjust this query based on how you define "related")
    related_items = Item.objects.filter(category=category).exclude(id=item.id)[:4]

    context = {
        'categories': categories,  # Add this line to pass categories to the template
        'category': category,
        'item': item,
        'sizes_with_stock': sizes_with_stock,
        'total_quantity': total_quantity,
        'related_items': related_items,  # Add this line
    }
    
    return render(request, 'product_single_view.html', context)
    
def view_more_category(request, category_id):
    # Fetch all categories
    categories = Category.objects.all()
    
    # Fetch the current category and related data
    category = get_object_or_404(Category, id=category_id)
    subcategories = category.subcategory_set.all()
    
    selected_subcategory_id = request.GET.get('subcategory')
    if selected_subcategory_id:
        subcategory = get_object_or_404(SubCategory, id=selected_subcategory_id)
        items = subcategory.items.all()
    else:
        items = category.items.all()
    
    context = {
        'categories': categories,  # Add this line to pass categories to the template
        'current_category': category,
        'subcategories': subcategories,
        'items': items,
        'selected_subcategory_id': selected_subcategory_id,
    }
    return render(request, 'view_more_category.html', context)
    
    
def product_details(request, category_id, item_id):
    item = Item.objects.filter(id=item_id, category_id=category_id).first()
    
    if not item:
        return HttpResponseNotFound("Product not found")
    
    return render(request, 'product_details.html', {
        'item': item,
    })
    


def get_team_details(team_id, api_key):
    url = f'https://api.football-data.org/v4/teams/{team_id}'
    headers = {'X-Auth-Token': api_key}
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else {}



@never_cache
def index(request):
    # Fetch all news and sort them by date
    all_news = News.objects.all().order_by('-date_created')
    
    # Get the latest news
    latest_news = all_news.first() if all_news.exists() else None
    
    # Get the top 3 news items
    top_news = all_news[1:4]  # Exclude the latest news and get the next 3
    
    # Get the next 4 news items
    bottom_news = all_news[4:8]  # Skip the first 4 items (latest + top 3) and take the next 4

    # Initialize context with default user data
    context = {
        'user_name': None,
        'user_email': None,
        'user_phone': None,
        'latest_news': latest_news,
        'top_news': top_news,
        'bottom_news': bottom_news,
    }

    # Check if the user is authenticated by session or social account
    if request.user.is_authenticated:
        user = request.user
        context.update({
            'user_name': user.username,
            'user_email': user.email,
            'user_phone': getattr(user, 'phone', None),  # Optional: if you have a phone field in the User model
        })
    elif 'user_id' in request.session:
        try:
            user = Users.objects.get(id=request.session['user_id'])
            context.update({
                'user_name': user.name,
                'user_email': user.email,
                'user_phone': user.phone,  # Add other user-specific details if needed
            })
        except Users.DoesNotExist:
            # Handle the case where the user is not found in the database
            pass
    elif request.user.is_authenticated:
        try:
            # Fetch user info from social account
            social_account = SocialAccount.objects.get(user=request.user)
            context.update({
                'user_name': social_account.extra_data.get('name', None),
                'user_email': social_account.extra_data.get('email', None),
            })
        except SocialAccount.DoesNotExist:
            # Handle case where social account is not found
            pass

    # Fetch fixtures from the football-data.org API
    api_key = 'dc93cd61f7a04a67be5652fc72195459'
    url = 'https://api.football-data.org/v4/teams/86/matches'  # Real Madrid's ID is 86
    headers = {'X-Auth-Token': api_key}

    response = requests.get(url, headers=headers)
    all_fixtures = response.json().get('matches', [])

    # Convert UTC dates to IST and filter for upcoming events
    ist_timezone = pytz.timezone('Asia/Kolkata')
    current_time = timezone.now()
    upcoming_fixtures = []

    for fixture in all_fixtures:
        utc_date = parse_datetime(fixture['utcDate'])
        if utc_date:
            # Make the datetime aware if it's naive
            if utc_date.tzinfo is None:
                utc_date = make_aware(utc_date)
            
            # Only process if the fixture is in the future
            if utc_date > current_time:
                # Convert to IST
                ist_date = utc_date.astimezone(ist_timezone)
                
                # Format the date as a string
                fixture['ist_date'] = ist_date.strftime("%a, %b %d, %Y, %I:%M %p IST")
                upcoming_fixtures.append(fixture)

    # Sort upcoming fixtures by date
    upcoming_fixtures.sort(key=lambda x: parse_datetime(x['utcDate']))

    # Add fixtures to the context
    context['fixtures'] = upcoming_fixtures

    return render(request, 'index.html', context)

    
def user_view_news(request, id):
    news_item = get_object_or_404(News, id=id)
    context = {
        'news': news_item
    }
    if request.user.is_authenticated:
        user = request.user
        context.update({
            'user_name': user.username,
            'user_email': user.email,
            'user_phone': getattr(user, 'phone', None),  # Optional: if you have a phone field in the User model
        })
    elif 'user_id' in request.session:
        try:
            user = Users.objects.get(id=request.session['user_id'])
            context.update({
                'user_name': user.name,
                'user_email': user.email,
                'user_phone': user.phone,  # Add other user-specific details if needed
            })
        except Users.DoesNotExist:
            pass
    return render(request, 'user_view_news.html', context)
    
def generate_otp():
    return random.randint(1000, 9999)

def position_list(request):
    positions = Position.objects.all()
    return render(request, 'admin_add_player.html', {'position_list': positions})


def admin_show_news(request):
        # Fetch all news items
    all_news = News.objects.all().order_by('-date_created')
    
    # Set up pagination
    paginator = Paginator(all_news, 4)  # Show 8 news items per page
    page_number = request.GET.get('page')  # Get the current page number from the request
    news_items = paginator.get_page(page_number)

    # Determine the latest 8 news items
    latest_news_ids = [news.id for news in all_news[:8]]

    # Determine the latest news item
    latest_news = all_news.first() if all_news.exists() else None

    context = {
        'news_items': news_items,
        'latest_news': latest_news,
        'latest_news_ids': latest_news_ids,  # Pass this to the template
        'paginator': paginator,
    }
    return render(request, 'admin_show_news.html', context)


def admin_add_news(request):
    return render(request,'admin_add_news.html')

@never_cache
def profile(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        if request.user.is_authenticated:
            if request.user.is_superuser:
                # For admin users, handle normally if needed
                user_id = request.session.get('user_id')
            else:
                # For normal and social users
                user_id = request.user.id
        else:
            user_id = request.session.get('user_id')

        try:
            user = Users.objects.get(id=user_id)
            user.name = name
            user.phone = phone
            user.save()
            messages.success(request, 'Profile updated successfully.')

            context = {
                'user_name': user.name,
                'user_email': user.email,
                'user_phone': user.phone,
            }
            return render(request, 'profile.html', context)
        except Users.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('login')  # Redirect to login if user not found
    else:
        if request.user.is_authenticated:
            user_id = request.user.id
        else:
            user_id = request.session.get('user_id')

        try:
            user = Users.objects.get(id=user_id)
            context = {
                'user_name': user.name,
                'user_email': user.email,
                'user_phone': user.phone,
            }
            return render(request, 'profile.html', context)
        except Users.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('login')  # Redirect to login if user not found

def logout(request):
    # Clear session variables on logout
    request.session.flush()
    return redirect('login')


def forgotpassword(request):
    return render(request,'forgotpassword.html')





def password_reset(request):
    return render(request,'password_reset.html')



def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Check for special case
        if email == 'realmadridfcwebsite@gmail.com' and password == 'Realmadrid@12':
            # Redirect to the admin dashboard directly
            return redirect('admin_dashboard')

        try:
            # First try standard user authentication
            user = Users.objects.get(email=email)
            if check_password(password, user.password):  # Check hashed password
                # Initialize session variables
                request.session['user_id'] = user.id
                request.session['user_name'] = user.name
                request.session['user_type'] = 'standard'  # Mark as standard user
                request.session.save()
                return redirect('index')
            
        except Users.DoesNotExist:
            # If user not found in Users table, try PlayerCredentials
            try:
                player_cred = PlayerCredentials.objects.get(email=email)
                if check_password(password, player_cred.password):  # Check hashed password
                    # Initialize session variables for player
                    request.session['user_id'] = player_cred.player.id
                    request.session['user_name'] = player_cred.player.player_name
                    request.session['user_type'] = 'player'  # Mark as player
                    request.session.save()
                    return redirect('player_dashboard')  # Redirect to player dashboard instead of index
                else:
                    messages.error(request, "Invalid email or password.", extra_tags='login_error')
            except PlayerCredentials.DoesNotExist:
                messages.error(request, "Invalid email or password.", extra_tags='login_error')

        # If we get here, either the password was wrong or neither type of user was found
        messages.error(request, "Invalid email or password.", extra_tags='login_error')

    return render(request, 'login.html')


import json
from django.shortcuts import render, redirect
from .models import QuizQuestion

@login_required
@csrf_exempt
def admin_player_game(request):
    # Fetch all uploaded images
    uploaded_images = UploadedImage.objects.all()  # Assuming UploadedImage is your model for storing images
    return render(request, 'admin_player_game.html', {'uploaded_images': uploaded_images})


def admin_gamification(request):
    # Fetch all quiz questions
    quiz_questions = QuizQuestion.objects.all()

    # Render the page with the fetched questions
    return render(request, 'admin_gamification.html', {'quiz_questions': quiz_questions})


def admin_guess_player(request):
    if request.method == 'POST':
        player_name = request.POST['player_name']
        player_image = request.FILES['player_image']
        
        # Create a new IdentifyPlayer instance and save it
        identify_player = IdentifyPlayer(name=player_name, image=player_image)
        identify_player.save()
        
        return redirect('admin_dashboard')  # Redirect to a success page or dashboard

    # Fetch all existing IdentifyPlayer records
    players = IdentifyPlayer.objects.all()  # Fetch players from the database
    context = {
        'players': players,  # Pass players to the template
    }
    return render(request, 'admin_guess_player.html', context)  # Render the template with context

def register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        try:
            # Generate OTP and store user data in session
            otp = generate_otp()
            request.session['otp'] = otp
            request.session['user_data'] = {
                'name': name,
                'email': email,
                'phone': phone,
                'password': make_password(password),  # Hashing the password
            }
            request.session['user_email'] = email  # Store email for OTP verification page
            request.session.save()

            # Send OTP to user's email
            send_mail(
                'Your OTP for signing in',
                f'Your OTP is {otp}',
                'your-email@gmail.com',  # Update with your actual email
                [email],
                fail_silently=False,
            )

            # Redirect to verify_otp with user_id parameter
            return redirect(reverse('email_otp_verif'))  # Assuming you have a URL named 'email_otp_verif'

        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return redirect('register')  # Redirect to the same registration page on error

    return render(request, 'register.html')


def email_otp_verif(request):
    if request.method == 'POST':
        otp1 = request.POST.get('otp1', '')
        otp2 = request.POST.get('otp2', '')
        otp3 = request.POST.get('otp3', '')
        otp4 = request.POST.get('otp4', '')

        entered_otp = otp1 + otp2 + otp3 + otp4
        entered_otp = int(entered_otp)
        session_otp = request.session.get('otp')  # Fetch the stored OTP from session
        user_email = request.session.get('user_email')  # Fetch the user's email from session

        # For debugging purposes, print the OTP values
        print(f"Entered OTP: {entered_otp}, Session OTP: {session_otp}")

        if entered_otp == session_otp:
            try:
                # Save user to the database
                user_data = request.session.get('user_data', {})
                user = Users.objects.create(
                    name=user_data.get('name'),
                    email=user_data.get('email'),
                    phone=user_data.get('phone'),
                    password=user_data.get('password'),  # Note: This should be hashed already
                )
                user.save()
                messages.success(request, 'OTP verified successfully. You can now log in.')
                return redirect('login')  # Redirect to login page after successful registration
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
        else:
            print(f"Entered OTP: {entered_otp}, Session OTP: {session_otp}")

            messages.error(request, f'Invalid OTP.Please try again.')
            return render(request, 'email_otp_verif.html', {'user_email': user_email})

    return render(request, 'email_otp_verif.html', {'user_email': request.session.get('user_email')})





@csrf_exempt
def forgotpassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = Users.objects.get(email=email)
            
            token = token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            
            reset_url = reverse('password_reset', kwargs={'uidb64': uidb64, 'token': token})
            reset_url = request.build_absolute_uri(reset_url)
            
            send_mail(
                'Password Reset Request',
                f'Click the following link to reset your password: {reset_url}',
                'your-email@gmail.com',
                [email],
                fail_silently=False,
            )
            
            return JsonResponse({'message': 'Password reset email has been sent. Check your email to proceed.'}, status=200)
        
        except Users.DoesNotExist:
            return JsonResponse({'error': 'User does not exist.'}, status=400)

    return render(request, 'password_reset/forgotpassword.html')

logger = logging.getLogger(__name__)


def password_reset(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Users.objects.get(pk=uid)
        
        if token_generator.check_token(user, token):
            if request.method == 'POST':
                new_password = request.POST['new_password']
                confirm_password = request.POST['confirm_password']
                
                if new_password == confirm_password:
                    user.password = make_password(new_password)
                    user.save()
                    logger.info(f'Password updated for user {user.pk}')
                    return redirect('login')
                else:
                    messages.error(request, 'Passwords do not match. Please try again.')
                    return render(request, 'password_reset/password_reset.html', {'uidb64': uidb64, 'token': token})
            
            return render(request, 'password_reset/password_reset.html', {'uidb64': uidb64, 'token': token})
        
        else:
            messages.error(request, 'Invalid password reset link.')
            return redirect('login')
    
    except (TypeError, ValueError, OverflowError, Users.DoesNotExist) as e:
        logger.error(f'Error during password reset: {e}')
        messages.error(request, 'Invalid password reset link.')
        return redirect('login')




@csrf_exempt  # Use csrf_exempt decorator to skip CSRF token requirement for this view (for testing purposes)
def check_email_availability(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        email = request.POST.get('email', None)
        logger.info(f"Checking availability for email: {email}")
        if email:
            try:
                user = Users.objects.get(email=email)
                logger.info(f"User found: {user.email}")
                return JsonResponse({'available': False})
            except Users.DoesNotExist:
                logger.info("No user found with this email")
                return JsonResponse({'available': True})
            except Exception as e:
                logger.error(f"Error checking email: {str(e)}")
                return JsonResponse({'error': str(e)}, status=500)
    logger.warning("Invalid request received")
    return JsonResponse({'error': 'Invalid request'}, status=400)




import requests
from django.conf import settings

def previous_results(request):
    api_key = 'dc93cd61f7a04a67be5652fc72195459'
    url = 'https://api.football-data.org/v4/teams/86/matches'  # Real Madrid's ID is 86
    headers = {'X-Auth-Token': api_key}

    response = requests.get(url, headers=headers)
    matches = response.json().get('matches', [])

    # Filter for past matches
    past_matches = [
        {
            'home_team': match['homeTeam']['name'],
            'away_team': match['awayTeam']['name'],
            'score': match['score'],
            'utc_date': parse_datetime(match['utcDate']),
        }
        for match in matches if match['status'] == 'FINISHED'
    ]

    # Prepare context with past match details
    context = {
        'past_matches': past_matches,
    }
    
    # Add user context
    if request.user.is_authenticated:
        user = request.user
        context.update({
            'user_name': user.username,
            'user_email': user.email,
            'user_phone': getattr(user, 'phone', None),
        })
    elif 'user_id' in request.session:
        try:
            user = Users.objects.get(id=request.session['user_id'])
            context.update({
                'user_name': user.name,
                'user_email': user.email,
                'user_phone': user.phone,
            })
        except Users.DoesNotExist:
            pass

    return render(request, 'previous_results.html', context)



def match_details(request, fixture_id):
    api_key = settings.API_FOOTBALL_KEY
    context = {
        'fixture_id': fixture_id,
        'api_football_key': api_key,
    }
    return render(request, 'match_details.html', context)


@csrf_exempt  # Use this if you are not using CSRF tokens in your AJAX requests
def add_quiz_question(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question_text = data.get('question')
            options = data.get('options')
            correct_answer = data.get('correctAnswer')

            # Create a new QuizQuestion instance
            quiz_question = QuizQuestion(
                question_text=question_text,
                options=options,
                correct_answers=[correct_answer]  # Store the correct answer as a list
            )
            quiz_question.save()  # Save the question to the database

            # Add success message alert
            messages.success(request, 'Question added successfully!')  # Add this line

            return JsonResponse({'success': True, 'message': 'Question added successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

def upload_image(request):
    if request.method == 'POST' and request.FILES['image']:
        image = request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(image.name, image)  # Save the file
        UploadedImage.objects.create(image=filename)  # Save the filename to the database
        return redirect('admin_player_game')  # Redirect after upload
    return render(request, 'admin_player_game.html')  # Render the same page if not POST



def upload_identify_player(request):
    if request.method == 'POST':
        player_name = request.POST['player_name']
        player_image = request.FILES['player_image']
        
        # Create a new IdentifyPlayer instance and save it
        identify_player = IdentifyPlayer(name=player_name, image=player_image)
        identify_player.save()
        
        return redirect('admin_guess_player')  # Redirect to a success page or dashboard

    # Fetch all existing IdentifyPlayer records
    players = IdentifyPlayer.objects.all()  # Fetch players from the database
    context = {
        'players': players,  # Pass players to the template
    }
    return render(request, 'admin_guess_player.html', context)  # Render the template with context


def gamezone(request):
    return render(request,'gamezone.html')

def gamezone_quiz(request):
    try:
        # Fetch all questions from the QuizQuestion model
        questions = list(QuizQuestion.objects.all())
        
        if not questions:
            logger.warning("No questions found in the database.")
            return render(request, 'gamezone_quiz.html', {'questions': []})

        # Ensure we don't exceed available questions
        random_questions = random.sample(questions, min(10, len(questions)))  

        # Prepare the context with questions, their options, and correct answers
        context = {
            'questions': [
                {
                    'question_text': question.question_text,
                    'options': question.options,
                    'correct_answer': question.correct_answers[0]  # Assuming correct_answers is a list of indices
                }
                for question in random_questions
            ]
        }

        # Render the template with the random questions and their options
        return render(request, 'gamezone_quiz.html', context)
    
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Error fetching quiz questions: {str(e)}")
        return render(request, 'gamezone_quiz.html', {'questions': []})  # Return an empty list on error
    
    
import random

def gamezone_guess(request):
    # Fetch all players from the IdentifyPlayer model
    players = IdentifyPlayer.objects.all()
    
    if not players:
        return render(request, 'gamezone_guess.html', {'error': 'No players found.'})

    # Randomly select a player for the current guess
    current_player = random.choice(players)

    context = {
        'current_player': current_player,  # Pass the selected player to the template
    }
    
    return render(request, 'gamezone_guess.html', context)


def gamezone_jigsaw(request):
    # Fetch all uploaded images
    uploaded_images = UploadedImage.objects.all()  # Fetch all images
    tiles = []

    if uploaded_images:
        # Randomly select an uploaded image
        uploaded_image = random.choice(uploaded_images)  # Select a random image

        # Load the image using PIL
        image_path = os.path.join(settings.MEDIA_ROOT, uploaded_image.image.name)
        image = Image.open(image_path)

        # Define the number of tiles (e.g., 3x3)
        tile_size = (image.width // 3, image.height // 3)  # Change to 3 tiles

        # Create the tiles directory if it doesn't exist
        tiles_directory = os.path.join(settings.MEDIA_ROOT, 'tiles')
        os.makedirs(tiles_directory, exist_ok=True)  # Create the directory

        # Split the image into tiles
        for i in range(3):  # 3 rows
            for j in range(3):  # 3 columns
                left = j * tile_size[0]
                upper = i * tile_size[1]
                right = left + tile_size[0]
                lower = upper + tile_size[1]

                # Create a tile
                tile = image.crop((left, upper, right, lower))
                tile_path = os.path.join(tiles_directory, f'tile_{i}_{j}.png')
                tile.save(tile_path)  # Save the tile image

                # Append the tile path to the list
                tiles.append(f'tiles/tile_{i}_{j}.png')

    context = {
        'tiles': tiles,  # Pass the list of tile paths to the template
        'MEDIA_URL': settings.MEDIA_URL,  # Add MEDIA_URL to context
    }
    return render(request, 'gamezone_jigsaw.html', context)



def dynamic_stadium(request, match_id):
    match = get_object_or_404(Match, match_id=match_id)
    
    # Get all stands and their sections
    stands = Stand.objects.all()
    stands_sections = {}
    for stand in stands:
        sections = Section.objects.filter(stand=stand)
        stands_sections[stand] = sections

    # Get all booked seats for this match
    # Only consider tickets that are not cancelled and not marked as available
    booked_seats = set()
    ticket_items = TicketItem.objects.filter(
        order__match=match
    ).exclude(
        order__status='Cancelled'  # Exclude cancelled orders
    ).exclude(
        is_available=True  # Exclude tickets marked as available
    )
    
    for item in ticket_items:
        stand_code = item.stand.name[0]  # First letter of stand name (N, S, E, W)
        booked_seats.add(f"{stand_code}-{item.seat_number}")

    # Convert kickoff time to IST and format it
    ist_timezone = pytz.timezone('Asia/Kolkata')
    kickoff_time = match.utc_date.astimezone(ist_timezone)
    formatted_kickoff_time = kickoff_time.strftime('%B %d, %Y %I:%M %p IST')

    context = {
        'match': {
            'id': match.match_id,
            'home_team': match.home_team,
            'away_team': match.away_team,
            'competition': match.competition,
            'kickoff_time': formatted_kickoff_time,  # Use the formatted time
            'venue': match.venue or 'Santiago Bernabéu',
        },
        'stands_sections': stands_sections,
        'booked_seats': list(booked_seats),  # Convert set to list for JSON serialization
    }

    if request.user.is_authenticated:
        user = request.user
        context.update({
            'user_name': user.username,
            'user_email': user.email,
            'user_phone': getattr(user, 'phone', None),
        })
    elif 'user_id' in request.session:
        try:
            user = Users.objects.get(id=request.session['user_id'])
            context.update({
                'user_name': user.name,
                'user_email': user.email,
                'user_phone': user.phone,
            })
        except Users.DoesNotExist:
            pass

    return render(request, 'dynamic_stadium.html', context)

@login_required
@csrf_exempt
def admin_player_logins(request):
    players = Player.objects.all()
    return render(request, 'admin_player_logins.html', {'players': players})

@login_required
@csrf_exempt
def create_player_login(request):
    if request.method == 'POST':
        player_id = request.POST.get('player')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            player = Player.objects.get(id=player_id)
            
            # Check if player already has credentials
            if PlayerCredentials.objects.filter(player=player).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Player already has login credentials'
                })
            
            # Check if email is already in use
            if PlayerCredentials.objects.filter(email=email).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email is already in use'
                })
            
            # Create new credentials
            PlayerCredentials.objects.create(
                player=player,
                email=email,
                password=make_password(password)  # Hash the password
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Player login credentials created successfully'
            })
            
        except Player.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Player not found'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })


def player_dashboard(request):
    if request.session.get('user_type') != 'player':
        return redirect('login')
    
    # Get the player object
    player = Player.objects.get(id=request.session['user_id'])
    
    # Calculate task counts based on video status
    tasks_with_videos = PlayerTask.objects.filter(
        player=player
    ).prefetch_related('videos')

    pending_tasks_count = 0
    completed_tasks_count = 0

    for task in tasks_with_videos:
        latest_video = task.videos.order_by('-uploaded_at').first()
        if not latest_video or latest_video.status in ['failed', 'pending']:
            pending_tasks_count += 1
        elif latest_video.status == 'completed':
            completed_tasks_count += 1
        # If video status is 'processing', it's still considered pending
        elif latest_video.status == 'processing':
            pending_tasks_count += 1

    # Fetch fixtures from the football-data.org API
    api_key = 'dc93cd61f7a04a67be5652fc72195459'
    url = 'https://api.football-data.org/v4/teams/86/matches'  # Real Madrid's ID is 86
    headers = {'X-Auth-Token': api_key}

    try:
        response = requests.get(url, headers=headers)
        all_fixtures = response.json().get('matches', [])

        # Convert UTC dates to IST and filter for upcoming events
        ist_timezone = pytz.timezone('Asia/Kolkata')
        current_time = timezone.now()
        upcoming_fixtures = []

        for fixture in all_fixtures:
            utc_date = parse_datetime(fixture['utcDate'])
            if utc_date:
                # Make the datetime aware if it's naive
                if utc_date.tzinfo is None:
                    utc_date = make_aware(utc_date)
                
                # Only process if the fixture is in the future
                if utc_date > current_time:
                    # Convert to IST
                    ist_date = utc_date.astimezone(ist_timezone)
                    
                    # Format the date as a string
                    fixture['ist_date'] = ist_date.strftime("%a, %b %d, %Y, %I:%M %p IST")
                    upcoming_fixtures.append(fixture)

        # Sort upcoming fixtures by date and get the next fixture
        upcoming_fixtures.sort(key=lambda x: parse_datetime(x['utcDate']))
        next_match = upcoming_fixtures[0] if upcoming_fixtures else None

    except Exception as e:
        print(f"Error fetching next match: {e}")
        next_match = None

    # Fetch tasks assigned to the player
    assigned_tasks = PlayerTask.objects.filter(
        player=player
    ).order_by('-assigned_date')

    # Get video submissions for tasks
    task_videos = {}
    for task in assigned_tasks:
        video = PlayerVideo.objects.filter(task=task).first()
        if video:
            task_videos[task.id] = {
                'video_url': video.video.url if video.video else None,
                'processed_video_url': video.processed_video.url if video.processed_video else None,
                'trainer_comment': video.trainer_comment,
                'processed_at': video.processed_at
            }

    context = {
        'next_match': next_match,
        'assigned_tasks': assigned_tasks,
        'task_videos': task_videos,
        'pending_tasks_count': pending_tasks_count,
        'completed_tasks_count': completed_tasks_count,
    }
    
    return render(request, 'player_dashboard.html', context)

def trainer_assign_task(request):
    if request.method == 'POST':
        player_id = request.POST.get('player')
        exercise_type = request.POST.get('exercise_type')
        instructions = request.POST.get('instructions')
        repetitions = request.POST.get('repetitions')
        due_date = request.POST.get('due_date')

        try:
            player = Player.objects.get(id=player_id)
            task = PlayerTask.objects.create(
                player=player,
                exercise_type=exercise_type,
                instructions=instructions,
                repetitions=repetitions,
                due_date=due_date,
                status='pending'
            )
            messages.success(request, f'Task assigned successfully to {player.player_name}!')
            return redirect('trainer_assign_task')
        except Exception as e:
            messages.error(request, f'Error assigning task: {str(e)}')

    # Get recent tasks for display
    recent_tasks = PlayerTask.objects.select_related('player').order_by('-assigned_date')[:5]
    
    context = {
        'players': Player.objects.all(),
        'exercise_types': PlayerTask.EXERCISE_TYPES,
        'recent_tasks': recent_tasks,
    }
    return render(request, 'trainer_assign_task.html', context)

@csrf_exempt
def process_ticket_booking(request, match_id):
    """
    Process ticket booking after Razorpay payment
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        
        # Extract and log payment details
        razorpay_payment_id = data.get('razorpay_payment_id')
        booking_id = data.get('booking_id')
        seats = data.get('seats', [])
        amount = data.get('amount', 0)
        booking_fee = data.get('booking_fee', 0)
        total_amount = data.get('total_amount', 0)
        
        print(f"Processing booking: {booking_id}")
        print(f"Seats: {seats}")
        print(f"Payment ID: {razorpay_payment_id}")
        
        # Get match details
        try:
            match = Match.objects.get(match_id=match_id)
            print(f"Found match: {match}")
        except Match.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Match not found'})
        
        # Process each step separately to identify where the error occurs
        try:
            # Create ticket order
            ticket_order = TicketOrder.objects.create(
                order_number=booking_id,
                user_id=request.user.id if request.user.is_authenticated else None,
                match=match,
                full_name=request.user.name if request.user.is_authenticated else 'Guest',
                email=request.user.email if request.user.is_authenticated else '',
                phone=request.user.phone if request.user.is_authenticated else '',
                total_price=total_amount,
                booking_fee=booking_fee,
                status='Confirmed',
                is_paid=True
            )
            print(f"Created ticket order: {ticket_order.order_number}")
            
            # Calculate price per seat
            price_per_seat = Decimal(amount) / Decimal(len(seats)) if seats else Decimal('0.00')
            price_per_seat = price_per_seat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)  # Round to 2 decimal places
            
            # Process seats one by one
            for seat in seats:
                try:
                    print(f"Processing seat: {seat}")
                    
                    # Parse seat format (e.g., "N-1" for North Stand, seat 1)
                    parts = seat.split('-')
                    if len(parts) != 2:
                        print(f"Invalid seat format: {seat}")
                        continue
                        
                    stand_code, seat_number_str = parts
                    
                    # Convert seat_number to integer
                    try:
                        seat_number = int(seat_number_str)
                    except ValueError:
                        print(f"Invalid seat number: {seat_number_str}")
                        continue
                    
                    # Map stand code to stand object
                    stand_map = {
                        'N': 'North Stand',
                        'S': 'South Stand',
                        'E': 'East Stand',
                        'W': 'West Stand'
                    }
                    
                    stand_name = stand_map.get(stand_code, stand_code)
                    print(f"Stand name: {stand_name}")
                    
                    # Get or create stand
                    try:
                        stand = Stand.objects.get(name=stand_name)
                        print(f"Found existing stand: {stand}")
                    except Stand.DoesNotExist:
                        stand = Stand.objects.create(name=stand_name)
                        print(f"Created new stand: {stand}")
                    
                    # Get or create section
                    try:
                        section = Section.objects.filter(stand=stand).first()
                        if not section:
                            # Create with minimal required fields
                            section = Section.objects.create(
                                name=f"Default {stand_name}",
                                stand=stand,
                                price=Decimal('300.00'),
                                seats=[]  # Use empty list instead of json.dumps([])
                            )
                            print(f"Created new section: {section}")
                        else:
                            print(f"Found existing section: {section}")
                    except Exception as e:
                        print(f"Error creating section: {str(e)}")
                        raise
                    
                    # Create ticket item
                    try:
                        ticket_item = TicketItem.objects.create(
                            order=ticket_order,
                            stand=stand,
                            section=section,
                            seat_number=seat_number,  # Now properly converted to int
                            price=price_per_seat  # Now properly calculated and rounded
                        )
                        print(f"Created ticket item: {ticket_item}")
                    except IntegrityError as ie:
                        print(f"Integrity error creating ticket item: {str(ie)}")
                        # Check if this is a duplicate seat
                        existing = TicketItem.objects.filter(
                            order=ticket_order,
                            stand=stand,
                            section=section,
                            seat_number=seat_number
                        ).exists()
                        if existing:
                            print(f"Seat {seat_number} already exists for this order")
                        else:
                            raise
                    except Exception as e:
                        print(f"Error creating ticket item: {str(e)}")
                        print(f"Type: {type(e)}")
                        raise
                        
                except Exception as seat_error:
                    print(f"Error processing seat {seat}: {str(seat_error)}")
                    # Continue with next seat instead of failing the whole booking
                    continue
            
            # Create payment record
            payment = TicketPayment.objects.create(
                ticket_order=ticket_order,
                payment_method='Razorpay',
                razorpay_payment_id=razorpay_payment_id,
                transaction_id=razorpay_payment_id,
                amount_paid=total_amount,
                status='Completed',
                completed_at=timezone.now()
            )
            print(f"Created payment record: {payment}")
            
            return JsonResponse({
                'success': True,
                'order_number': ticket_order.order_number,
                'redirect_url': f'/booking-success/{ticket_order.order_number}/'
            })
            
        except Exception as process_error:
            print(f"Error in booking process: {str(process_error)}")
            raise
    
    except Exception as e:
        print(f"Error processing ticket booking: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})



def player_detail(request, player_id):
    # Fetch the player and related data
    player = get_object_or_404(Player, id=player_id)
    season_stats = SeasonStats.objects.filter(player=player)
    player_history = PlayerHistory.objects.filter(player=player)
    achievements = PlayerAchievement.objects.filter(player=player)
    
    context = {
        'player': player,
        'season_stats': season_stats,
        'player_history': player_history,
        'achievements': achievements,
    }
    return render(request, 'player_detail.html', context)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Player, Position

@csrf_exempt
def admin_add_player(request):
    if request.method == 'POST':
        try:
            # Create new player object
            player = Player(
                jersey_num=request.POST.get('jersey_num'),
                player_name=request.POST.get('player_name'),
                player_country=request.POST.get('player_country'),
                player_position=Position.objects.get(id=request.POST.get('player_position')),
                player_role=request.POST.get('player_role'),
                date_of_birth=request.POST.get('date_of_birth') or None,
                height=request.POST.get('height') or None,
                weight=request.POST.get('weight') or None,
                appearances=request.POST.get('appearances', 0),
                goals=request.POST.get('goals', 0),
                assists=request.POST.get('assists', 0),
                clean_sheets=request.POST.get('clean_sheets', 0),
                yellow_cards=request.POST.get('yellow_cards', 0),
                red_cards=request.POST.get('red_cards', 0),
                biography=request.POST.get('biography', ''),
                joined_date=request.POST.get('joined_date') or None,
                contract_end_date=request.POST.get('contract_end_date') or None,
            )

            if 'player_image' in request.FILES:
                player.player_image = request.FILES['player_image']

            player.save()

            # Create season stats if provided
            season = request.POST.get('season')
            competition = request.POST.get('competition')
            if season and competition:
                SeasonStats.objects.create(
                    player=player,
                    season=season,
                    competition=competition,
                    appearances=request.POST.get('appearances', 0),
                    goals=request.POST.get('goals', 0),
                    assists=request.POST.get('assists', 0),
                    minutes_played=request.POST.get('minutes_played', 0)
                )
            
            # Handle achievements
            achievements = json.loads(request.POST.get('achievements', '[]'))
            for achievement in achievements:
                PlayerAchievement.objects.create(
                    player=player,  # player object from your existing code
                    title=achievement['title'],
                    description=achievement['description'],
                    date=achievement['date'] if achievement['date'] else None
                )

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # For GET requests, render the template
    positions = Position.objects.all()
    return render(request, 'admin_add_player.html', {'positions': positions})

# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

@csrf_exempt
@require_POST
def create_temp_booking(request, match_id):
    """
    Create a temporary booking and initialize Razorpay order
    """
    try:
        data = json.loads(request.body)
        seats = data.get('seats', [])
        amount = data.get('amount', 0)
        
        if not seats:
            return JsonResponse({'success': False, 'error': 'No seats selected'})
        
        # Get match details
        try:
            match = Match.objects.get(match_id=match_id)
        except Match.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Match not found'})
        
        # Check if seats are already booked
        # This assumes your seats are stored in the format "Stand-Number" (e.g., "N-1")
        booked_tickets = TicketItem.objects.filter(
            order__match=match, 
            order__status__in=['Confirmed', 'Payment_Initiated']
        ).values_list('seat_number', flat=True)
        
        # Convert booked_tickets to the same format as incoming seats for comparison
        formatted_booked_tickets = [f"{ticket}" for ticket in booked_tickets]
        unavailable_seats = [seat for seat in seats if seat in formatted_booked_tickets]
        
        if unavailable_seats:
            return JsonResponse({
                'success': False, 
                'error': f'Seats {", ".join(unavailable_seats)} are no longer available'
            })
        
        # Generate a unique booking ID
        booking_id = str(uuid.uuid4())
        
        # Calculate booking fee (5% of total amount)
        booking_fee = round(amount * 0.05, 2)
        total_amount = amount + booking_fee
        
        # Create Razorpay order
        razorpay_order = razorpay_client.order.create({
            'amount': int(total_amount * 100),  # Amount in paise
            'currency': 'INR',
            'receipt': booking_id,
            'payment_capture': 1  # Auto-capture payment
        })
        
        # Store temporary booking data in cache
        # Cache key will expire after 15 minutes (900 seconds)
        temp_booking = {
            'booking_id': booking_id,
            'match_id': match_id,
            'seats': seats,
            'amount': amount,
            'booking_fee': booking_fee,
            'total_amount': total_amount,
            'razorpay_order_id': razorpay_order['id'],
            'user_id': request.user.id if request.user.is_authenticated else None,
            'timestamp': str(timezone.now())
        }
        
        cache.set(f'temp_booking_{booking_id}', temp_booking, 900)
        
        # Get user details for Razorpay prefill
        user_name = ""
        user_email = ""
        user_phone = ""
        
        if request.user.is_authenticated:
            user_name = request.user.name
            user_email = request.user.email
            user_phone = request.user.phone
        
        return JsonResponse({
            'success': True,
            'booking_id': booking_id,
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'order_id': razorpay_order['id'],
            'amount': int(total_amount * 100),  # Amount in paise
            'user_name': user_name,
            'user_email': user_email,
            'user_phone': user_phone
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def verify_payment(request):
    """
    Verify Razorpay payment and confirm booking
    """
    try:
        data = json.loads(request.body)
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        booking_id = data.get('booking_id')
        
        # Verify the payment signature
        params_dict = {
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
        except Exception:
            return JsonResponse({'success': False, 'error': 'Invalid payment signature'})
        
        # Get the temporary booking from cache
        temp_booking = cache.get(f'temp_booking_{booking_id}')
        
        if not temp_booking:
            return JsonResponse({'success': False, 'error': 'Booking expired or not found'})
        
        # Process the confirmed booking
        with transaction.atomic():
            # Get match
            match = Match.objects.get(match_id=temp_booking['match_id'])
            
            # Create ticket order
            ticket_order = TicketOrder.objects.create(
                user_id=temp_booking['user_id'],
                match=match,
                full_name=data.get('user_name', 'Guest'),
                email=data.get('user_email', ''),
                phone=data.get('user_phone', ''),
                total_price=temp_booking['total_amount'],
                booking_fee=temp_booking['booking_fee'],
                status='Confirmed',
                razorpay_order_id=razorpay_order_id,
                is_paid=True
            )
            
            # Create ticket items
            for seat in temp_booking['seats']:
                # Parse seat format (e.g., "N-1" for North Stand, seat 1)
                stand_code, seat_number = seat.split('-')
                
                # Map stand code to stand object
                stand_map = {
                    'N': 'North',
                    'S': 'South',
                    'E': 'East',
                    'W': 'West'
                }
                
                stand_name = stand_map.get(stand_code, stand_code)
                
                # Get stand and section
                stand = Stand.objects.get(name=stand_name)
                # Assuming you have a default section for each stand
                section = Section.objects.filter(stand=stand).first()
                
                # Create ticket item
                TicketItem.objects.create(
                    order=ticket_order,
                    stand=stand,
                    section=section,
                    seat_number=seat_number,
                    price=temp_booking['amount'] / len(temp_booking['seats'])
                )
            
            # Create payment record
            TicketPayment.objects.create(
                ticket_order=ticket_order,
                payment_method='Razorpay',
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
                razorpay_signature=razorpay_signature,
                transaction_id=razorpay_payment_id,
                amount_paid=temp_booking['total_amount'],
                status='Completed',
                completed_at=timezone.now()
            )
            
            # Clear the temporary booking from cache
            cache.delete(f'temp_booking_{booking_id}')
            
            return JsonResponse({
                'success': True,
                'redirect_url': f'/booking-success/{ticket_order.order_number}/'
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def cancel_temp_booking(request):
    """
    Cancel a temporary booking
    """
    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        
        if not booking_id:
            return JsonResponse({'success': False, 'error': 'Booking ID is required'})
        
        # Delete the temporary booking from cache
        cache.delete(f'temp_booking_{booking_id}')
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def generate_ticket_pdf(request, order_id):
    # Get the ticket order details
    ticket_order = get_object_or_404(TicketOrder, id=order_id)
    ticket_items = TicketItem.objects.filter(order=ticket_order)
    match = ticket_order.match
    
    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    
    # Set up fonts - try to load premium fonts
    font_dir = os.path.join(settings.STATIC_ROOT, 'fonts')
    try:
        # Register premium fonts
        pdfmetrics.registerFont(TTFont('Montserrat', os.path.join(font_dir, 'Montserrat-Regular.ttf')))
        pdfmetrics.registerFont(TTFont('MontserratBold', os.path.join(font_dir, 'Montserrat-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('MontserratSemiBold', os.path.join(font_dir, 'Montserrat-SemiBold.ttf')))
        pdfmetrics.registerFont(TTFont('MontserratLight', os.path.join(font_dir, 'Montserrat-Light.ttf')))
        
        base_font = "Montserrat"
        bold_font = "MontserratBold"
        semibold_font = "MontserratSemiBold"
        light_font = "MontserratLight"
    except:
        # Fallback to standard fonts
        base_font = "Helvetica"
        bold_font = "Helvetica-Bold"
        semibold_font = "Helvetica-Bold"
        light_font = "Helvetica"
        
    # Real Madrid premium color palette
    rm_blue = HexColor('#0B2C5F')  # Dark blue
    rm_gold = HexColor('#FCBB30')  # Gold
    rm_white = HexColor('#FFFFFF')  # White
    rm_navy = HexColor('#022044')  # Navy blue (darker)
    rm_silver = HexColor('#C0C0C0')  # Silver accent
    
    # Create the PDF object using a premium ticket size
    pagesize = (8.5*inch, 3.5*inch)  # Premium ticket dimensions
    p = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize
    
    # Load image assets
    logo_path = os.path.join(settings.STATIC_ROOT, 'images/real-madrid-logo.png')
    stadium_path = os.path.join(settings.STATIC_ROOT, 'images/bernabeu.jpg')
    pattern_path = os.path.join(settings.STATIC_ROOT, 'images/rm_pattern.png')
    trophy_path = os.path.join(settings.STATIC_ROOT, 'images/champions_trophy.png')
    player_path = os.path.join(settings.STATIC_ROOT, 'images/player_silhouette.png')
    
    # Process each ticket as a separate page with premium design
    for i, ticket in enumerate(ticket_items):
        # Main background gradient (dark blue to navy)
        p.setFillColorRGB(0.04, 0.13, 0.26)  # Start with dark blue
        p.rect(0, 0, width, height, fill=1, stroke=0)
        
        # Add decorative pattern if available
        if os.path.exists(pattern_path):
            p.saveState()
            p.setFillColorRGB(0.05, 0.16, 0.35, alpha=0.7)  # Slightly lighter blue with transparency
            p.drawImage(pattern_path, 0, 0, width=width, height=height, mask='auto')
            p.restoreState()
        
        # Add stadium image as a strip on the left
        if os.path.exists(stadium_path):
            p.drawImage(stadium_path, 0.3*cm, 0.3*cm, width=2.5*cm, height=height-0.6*cm, mask='auto')
            
            # Add overlay to ensure text is readable
            p.setFillColorRGB(0.04, 0.13, 0.26, alpha=0.6)  # Semi-transparent dark blue
            p.rect(0.3*cm, 0.3*cm, 2.5*cm, height-0.6*cm, fill=1, stroke=0)
        
        # Add decorative gold accent lines
        p.setStrokeColor(rm_gold)
        p.setLineWidth(1.5)
        p.line(3.1*cm, 0.3*cm, 3.1*cm, height-0.3*cm)  # Vertical line separating stadium image
        
        # Instead of using arc with stroke(), draw a curved line at top
        # This is a simpler approach that accomplishes a similar visual effect
        p.setStrokeColor(rm_gold)
        p.setLineWidth(2)
        
        # Draw multiple small line segments to create a curved effect at the top
        curve_start_x = 3.1*cm
        curve_end_x = width-0.6*cm
        curve_width = curve_end_x - curve_start_x
        curve_top = height-0.3*cm
        
        # Draw multiple small lines to simulate a curve (simple half-circle approximation)
        segments = 20
        for j in range(segments+1):
            x1 = curve_start_x + (j-1) * curve_width / segments
            y1 = curve_top - 0.8*cm * (1 - ((j-1)/segments*2-1)**2) if j > 0 else curve_top
            
            x2 = curve_start_x + j * curve_width / segments
            y2 = curve_top - 0.8*cm * (1 - ((j)/segments*2-1)**2)
            
            if j > 0:  # Skip first iteration as it would start from nowhere
                p.line(x1, y1, x2, y2)
        
        # Add Real Madrid logo with glowing effect
        if os.path.exists(logo_path):
            # Draw white circle behind logo for glow effect
            p.setFillColor(rm_white)
            p.circle(3.8*cm, height-0.8*cm, 0.65*cm, fill=1, stroke=0)
            
            # Draw the logo
            p.drawImage(logo_path, 3.2*cm, height-1.4*cm, width=1.2*cm, height=1.2*cm, mask='auto')
        
        # Add trophy icon if available
        if os.path.exists(trophy_path):
            p.drawImage(trophy_path, width-1.7*cm, height-1.4*cm, width=1.2*cm, height=1.2*cm, mask='auto')
        
        # Header text - Club name with emoji
        p.setFillColor(rm_white)
        p.setFont(bold_font, 14)
        p.drawString(4.7*cm, height-0.9*cm, "REAL MADRID C.F. 🏆")
        
        # Gold divider below header
        p.setStrokeColor(rm_gold)
        p.setLineWidth(0.5)
        p.line(3.3*cm, height-1.5*cm, width-0.3*cm, height-1.5*cm)
        
        # Match information - stylish card-like design
        # White card background with slight transparency
        p.setFillColorRGB(1, 1, 1, alpha=0.9)
        p.roundRect(3.3*cm, height-3.2*cm, width-3.6*cm, 1.5*cm, 3*mm, fill=1, stroke=0)
        
        # Match teams with vs in gold
        p.setFillColor(rm_blue)
        p.setFont(bold_font, 12)
        home_team = match.home_team
        away_team = match.away_team
        home_width = p.stringWidth(home_team, bold_font, 12)
        
        # Draw team names in blue with VS in gold
        team_y = height-2*cm
        p.drawString(3.5*cm, team_y, home_team)
        
        # VS in gold
        p.setFillColor(rm_gold)
        p.setFont(bold_font, 12)
        vs_text = "vs"
        vs_width = p.stringWidth(vs_text, bold_font, 12)
        vs_x = 3.5*cm + home_width + 0.3*cm
        p.drawString(vs_x, team_y, vs_text)
        
        # Away team
        p.setFillColor(rm_blue)
        p.drawString(vs_x + vs_width + 0.3*cm, team_y, away_team)
        
        # Competition with trophy emoji
        p.setFont(semibold_font, 10)
        p.setFillColor(rm_blue)
        comp_text = f"🏆 {match.competition}"
        p.drawCentredString((3.3*cm + width-3.6*cm)/2, height-2.5*cm, comp_text)
        
        # Date and time with emoji
        try:
            match_date = match.ist_date
            date_string = match_date.strftime("%d %b %Y")
            time_string = match_date.strftime("%I:%M %p")
            
            p.setFont(base_font, 8)
            date_text = f"📅 {date_string}"
            time_text = f"⏰ {time_string}"
            
            p.drawCentredString((3.3*cm + width-3.6*cm)/2, height-2.9*cm, date_text)
            p.drawCentredString((3.3*cm + width-3.6*cm)/2, height-3.1*cm, time_text)
        except:
            # Fallback if date processing fails
            p.setFont(base_font, 8)
            p.drawCentredString((3.3*cm + width-3.6*cm)/2, height-3*cm, "📅 Match Day")
        
        # Set up vertical "OFFICIAL MATCH TICKET" text on left side
        p.saveState()
        p.translate(1.5*cm, height/2)
        p.rotate(90)
        p.setFillColor(rm_white)
        p.setFont(bold_font, 12)
        p.drawCentredString(0, 0, "OFFICIAL MATCH TICKET")
        p.restoreState()
        
        # Player silhouette if available
        if os.path.exists(player_path):
            p.drawImage(player_path, width-3.3*cm, 0.4*cm, width=3*cm, height=height-0.8*cm, mask='auto')
            
            # Add overlay to ensure text is readable
            p.setFillColorRGB(0.04, 0.13, 0.26, alpha=0.7)  # Semi-transparent dark blue
            p.rect(width-3.3*cm, 0.4*cm, 3*cm, height-0.8*cm, fill=1, stroke=0)
        
        # Ticket details in an attractive card
        # Card background
        p.setFillColor(rm_white)
        p.roundRect(3.3*cm, 0.4*cm, width-6.6*cm, 1.6*cm, 3*mm, fill=1, stroke=0)
        
        # Card header
        p.setFillColor(rm_gold)
        p.roundRect(3.3*cm, 1.7*cm, width-6.6*cm, 0.3*cm, radius=3*mm, fill=1, stroke=0)
        
        # Header text
        p.setFillColor(rm_navy)
        p.setFont(bold_font, 8)
        p.drawCentredString(3.3*cm + (width-6.6*cm)/2, 1.75*cm, "TICKET DETAILS")
        
        # Ticket information
        p.setFillColor(rm_navy)
        
        # Two columns layout for ticket details
        col1_x = 3.5*cm
        col2_x = 5.0*cm
        
        # Row 1
        text_y = 1.4*cm
        p.setFont(semibold_font, 8)
        p.drawString(col1_x, text_y, "ORDER #:")
        p.setFont(base_font, 8)
        p.drawString(col2_x, text_y, f"{ticket_order.order_number[:8]}...")
        
        # Row 2
        text_y = 1.1*cm
        p.setFont(semibold_font, 8)
        p.drawString(col1_x, text_y, "STAND:")
        p.setFont(base_font, 8)
        p.drawString(col2_x, text_y, f"{ticket.stand.name}")
        
        # Row 3
        text_y = 0.8*cm
        p.setFont(semibold_font, 8)
        p.drawString(col1_x, text_y, "SECTION:")
        p.setFont(base_font, 8)
        p.drawString(col2_x, text_y, f"{ticket.section.name}")
        
        # Row 4
        text_y = 0.5*cm
        p.setFont(semibold_font, 8)
        p.drawString(col1_x, text_y, "SEAT:")
        p.setFont(base_font, 8)
        p.drawString(col2_x, text_y, f"{ticket.seat_number}")
        
        # Gold price bubble on right side
        price_x = width - 2.2*cm
        price_y = height/2
        
        # Gold circle for price
        p.setFillColor(rm_gold)
        p.circle(price_x, price_y, 0.9*cm, fill=1, stroke=0)
        
        # Price text
        p.setFillColor(rm_navy)
        p.setFont(bold_font, 12)
        price_text = f"₹{ticket.price}"
        price_width = p.stringWidth(price_text, bold_font, 12)
        p.drawString(price_x - price_width/2, price_y - 0.2*cm, price_text)
        
        # "PRICE" label
        p.setFont(semibold_font, 8)
        label_width = p.stringWidth("PRICE", semibold_font, 8)
        p.drawString(price_x - label_width/2, price_y + 0.3*cm, "PRICE")
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=0,
        )
        qr.add_data(f"{ticket_order.order_number}-{ticket.id}")
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img_path = os.path.join(settings.MEDIA_ROOT, f'qr_temp_{ticket_order.order_number}_{ticket.id}.png')
        qr_img.save(qr_img_path)
        
        # White background for QR code
        p.setFillColor(rm_white)
        p.roundRect(width-2.1*cm, 0.4*cm, 1.7*cm, 1.7*cm, 3*mm, fill=1, stroke=0)
        
        # Draw QR code
        p.drawImage(qr_img_path, width-2*cm, 0.5*cm, width=1.5*cm, height=1.5*cm, mask='auto')
        
        # Add scan text under QR
        p.setFont(base_font, 6)
        p.setFillColor(rm_navy)
        p.drawCentredString(width-1.25*cm, 0.3*cm, "SCAN FOR ENTRY 📱")
        
        # Add decorative element at bottom
        p.setStrokeColor(rm_gold)
        p.setLineWidth(1)
        p.line(0.3*cm, 0.15*cm, width-0.3*cm, 0.15*cm)
        
        # Add ticket info footer
        p.setFont(light_font, 5)
        p.setFillColor(rm_silver)
        terms = "✨ Keep this ticket safe • No refunds or exchanges • Subject to club terms & conditions • ⚽️ #HalaMadrid ⚽️"
        p.drawCentredString(width/2, 0.07*cm, terms)
        
        # Clean up temp QR file
        if os.path.exists(qr_img_path):
            os.remove(qr_img_path)
            
        if i < len(ticket_items) - 1:
            p.showPage()  # Add a new page for the next ticket
    
    # Close the PDF object cleanly
    p.showPage()
    p.save()
    
    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Real_Madrid_Tickets_{ticket_order.order_number}.pdf"'
    
    return response



def upload_task_video(request, task_id):
    task = get_object_or_404(PlayerTask, id=task_id)
    
    if request.method == 'POST' and request.FILES.get('video'):
        try:
            # Create new PlayerVideo instance
            player_video = PlayerVideo.objects.create(
                task=task,
                player=task.player,
                video=request.FILES['video'],
                status='pending',
                uploaded_at=timezone.now()
            )
            
            # Process video immediately
            try:
                logger.info(f"Starting video processing for video_id: {player_video.id}")
                process_exercise_video(player_video.id)
                return JsonResponse({
                    'success': True,
                    'video_id': player_video.id,
                    'message': 'Video uploaded and processing started.'
                })
            except Exception as e:
                logger.error(f"Processing error: {str(e)}")
                player_video.status = 'failed'
                player_video.error_message = str(e)
                player_video.save()
                return JsonResponse({
                    'success': False,
                    'error': f"Processing failed: {str(e)}"
                })
            
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f"Upload failed: {str(e)}"
            })

    return JsonResponse({
        'success': False,
        'error': 'Invalid request'
    })

def process_exercise_video(video_id):
    """Process exercise video with MediaPipe pose detection"""
    video = PlayerVideo.objects.get(id=video_id)
    video.status = 'processing'
    video.save()

    try:
        logger.info(f"Starting video processing for video ID: {video_id}")
        
        # Initialize MediaPipe
        logger.info("Initializing MediaPipe Pose")
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Open video file
        video_path = os.path.join(settings.MEDIA_ROOT, str(video.video))
        logger.info(f"Opening video file: {video_path}")
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at {video_path}")
            
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("Failed to open video file")

        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Video properties - FPS: {fps}, Width: {frame_width}, Height: {frame_height}, Total Frames: {total_frames}")

        # Create output video writer
        output_filename = f'processed_video_{video.id}.mp4'
        output_path = os.path.join(settings.MEDIA_ROOT, 'processed_videos', output_filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        logger.info(f"Creating output video file: {output_path}")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

        # Initialize exercise tracking
        exercise_counter = 0
        form_scores = []
        stage = None
        processed_frames = 0

        logger.info("Starting frame processing loop")
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            processed_frames += 1
            
            # Log progress every 100 frames
            if processed_frames % 100 == 0:
                progress = int((processed_frames / total_frames) * 100)
                logger.info(f"Processing progress: {progress}% ({processed_frames}/{total_frames} frames)")
                video.processing_progress = progress
                video.save()

            # Process frame with MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_frame)

            if results.pose_landmarks:
                # Draw pose landmarks
                mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS
                )

                # Get landmarks and analyze exercise
                landmarks = results.pose_landmarks.landmark
                exercise_type = video.task.exercise_type.lower()
                
                try:
                    if exercise_type == 'pushup':
                        form_score, rep_completed, stage = analyze_pushup(landmarks, stage)
                        if rep_completed:
                            logger.info(f"Pushup rep detected! Count: {exercise_counter + 1}")
                    # ... other exercise types ...

                    if rep_completed:
                        exercise_counter += 1
                        logger.info(f"Exercise rep completed. Total count: {exercise_counter}")

                    if form_score is not None:
                        form_scores.append(form_score)

                except Exception as e:
                    logger.error(f"Error analyzing frame {processed_frames}: {str(e)}")
                    continue

            # Write processed frame
            out.write(frame)

        logger.info(f"Frame processing complete. Total frames processed: {processed_frames}")

        # Cleanup
        cap.release()
        out.release()
        pose.close()

        # Calculate final metrics
        avg_form_score = np.mean(form_scores) if form_scores else 0
        completion_percentage = (exercise_counter / video.task.repetitions) * 100 if video.task.repetitions > 0 else 0

        metrics = {
            'total_repetitions': exercise_counter,
            'target_repetitions': video.task.repetitions,
            'completion_percentage': float(completion_percentage),
            'average_form_score': float(avg_form_score),
            'frames_processed': processed_frames
        }
        
        logger.info(f"Processing complete. Final metrics: {metrics}")

        # Update video record
        video.processed_video = f'processed_videos/{output_filename}'
        video.status = 'completed'
        video.processed_at = timezone.now()
        video.evaluation_data = metrics
        video.save()

        logger.info(f"Video {video_id} processed successfully")
        return True

    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}")
        video.status = 'failed'
        video.error_message = str(e)
        video.save()
        raise

def trainer_dashboard(request):
    # Get tasks assigned by this trainer
    tasks = PlayerTask.objects.filter(assigned_by=request.user).order_by('-assigned_date')
    
    # Group tasks by status
    pending_tasks = tasks.filter(status='pending')
    completed_tasks = tasks.filter(status='completed')
    evaluated_tasks = tasks.filter(status='evaluated')
    
    context = {
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'evaluated_tasks': evaluated_tasks
    }
    
    return render(request, 'trainer/dashboard.html', context)


def trainer_show_task(request):
    tasks = PlayerTask.objects.select_related('player', 'player__player_position').all()
    
    context = {
        'tasks': tasks,
        'tasks_stats': {
            'pending': tasks.filter(status='pending').count(),
            'completed': tasks.filter(status='completed').count(),
            'all': tasks.count(),
        }
    }
    return render(request, 'trainer_show_task.html', context)



from django.core.files.storage import default_storage
from django.conf import settings
import os
from celery import shared_task
import cv2
import numpy as np
import mediapipe as mp
from datetime import datetime

@shared_task
def process_video(video_id):
    """
    Background task to process video for exercise analysis
    """
    try:
        logger.info(f"Starting video processing for video_id: {video_id}")
        video = PlayerVideo.objects.get(id=video_id)
        video.status = 'processing'
        video.save()

        logger.info("Initializing MediaPipe Pose")
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Get video path and open
        video_path = os.path.join(settings.MEDIA_ROOT, str(video.video))
        logger.info(f"Opening video file: {video_path}")
        cap = cv2.VideoCapture(video_path)
        
        # Video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        processed_frames = 0
        exercise_type = video.task.exercise_type
        target_reps = video.task.repetitions
        
        # Analysis metrics
        rep_count = 0
        form_scores = []
        current_stage = None
        prev_landmarks = None

        logger.info(f"Total frames to process: {total_frames}")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            processed_frames += 1
            if processed_frames % 30 == 0:
                logger.info(f"Processing frame {processed_frames}/{total_frames}")
                progress = int((processed_frames / total_frames) * 100)
                video.processing_progress = progress
                video.save()

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_frame)

            if results.pose_landmarks:
                form_score, rep_completed, current_stage = analyze_exercise(
                    exercise_type,
                    results.pose_landmarks.landmark,
                    prev_landmarks,
                    current_stage
                )
                
                if rep_completed:
                    rep_count += 1
                form_scores.append(form_score)
                prev_landmarks = results.pose_landmarks.landmark

        # Calculate final metrics
        raw_form_score = sum(form_scores) / len(form_scores) if form_scores else 0
        completion_percentage = (rep_count / target_reps * 100) if target_reps > 0 else 0
        
        # First, calculate base form score with initial completion penalty
        if completion_percentage < 30:
            # Severe penalty for very low completion
            base_score = raw_form_score * 0.3  # Maximum 30% of raw score
        elif completion_percentage < 50:
            # Major penalty for low completion
            base_score = raw_form_score * 0.5  # Maximum 50% of raw score
        elif completion_percentage < 75:
            # Moderate penalty for partial completion
            base_score = raw_form_score * 0.75  # Maximum 75% of raw score
        elif completion_percentage < 90:
            # Minor penalty for near completion
            base_score = raw_form_score * 0.9  # Maximum 90% of raw score
        else:
            # No penalty for high completion
            base_score = raw_form_score

        # Now apply weighted scoring between form and completion
        form_weight = 0.6
        completion_weight = 0.4
        
        # Calculate weighted score
        avg_form_score = (
            (base_score * form_weight) +  # Form component (already penalized)
            (completion_percentage * completion_weight)  # Completion component
        )
        
        # Apply final scaling based on completion percentage
        completion_scaling = (completion_percentage / 100) ** 1.2  # Exponential scaling
        avg_form_score = avg_form_score * completion_scaling
        
        # Ensure the score cannot exceed completion percentage
        avg_form_score = min(avg_form_score, completion_percentage)
        
        # Set minimum score based on completion
        min_score = completion_percentage * 0.4  # Minimum score is 40% of completion rate
        avg_form_score = max(min_score, avg_form_score)

        # Round the final score
        avg_form_score = round(avg_form_score, 1)

        # Generate evaluation data with detailed breakdown
        evaluation_data = {
            'Repetitions Completed': rep_count,
            'Target Repetitions': target_reps,
            'Completion Rate': f"{round(completion_percentage, 1)}%",
            'Raw Form Score': f"{round(raw_form_score, 1)}%",
            'Base Score After Completion Penalty': f"{round(base_score, 1)}%",
            'Final Form Score': f"{round(avg_form_score, 1)}%",
            'Completion Impact': f"{round(completion_percentage, 1)}%"
        }

        # Generate automated feedback
        feedback = []

        # Completion feedback
        if completion_percentage >= 100:
            feedback.append("Excellent work! You've completed all required repetitions.")
        elif completion_percentage >= 75:
            feedback.append(f"Good effort! You completed {rep_count} out of {target_reps} repetitions.")
        else:
            feedback.append(f"Keep working! You completed {rep_count} out of {target_reps} repetitions.")

        # Form feedback based on exercise type
        if exercise_type == 'pushup':
            if avg_form_score >= 90:
                feedback.append("Your pushup form was excellent! Great body alignment and control.")
            elif avg_form_score >= 70:
                feedback.append("Good pushup form. Focus on keeping your core tight and maintaining a straight back.")
            else:
                feedback.append("Work on your pushup form. Keep your body straight and control the movement.")
        elif exercise_type == 'squat':
            if avg_form_score >= 90:
                feedback.append("Perfect squat depth and form! Your knee alignment was excellent.")
            elif avg_form_score >= 70:
                feedback.append("Good squat form. Try to maintain consistent depth and keep your knees aligned.")
            else:
                feedback.append("Focus on squat depth and keeping your knees aligned with your toes.")
        elif exercise_type == 'sprint':
            if avg_form_score >= 90:
                feedback.append("Excellent running form! Great knee drive and arm movement.")
            elif avg_form_score >= 70:
                feedback.append("Good running technique. Focus on maintaining consistent arm swing.")
            else:
                feedback.append("Work on your running form. Keep your arms relaxed and drive your knees.")

        # Add improvement suggestions
        if avg_form_score < 85:
            feedback.append("Areas for improvement:")
            if min(form_scores) < 70:
                feedback.append("- Pay attention to maintaining consistent form throughout the exercise")
            if completion_percentage < 90:
                feedback.append("- Build endurance to complete all repetitions")

        # Add encouragement
        feedback.append("\nKeep up the great work! Regular practice will lead to improvement. 💪")

        # Save results
        video.status = 'completed'
        video.processed_at = timezone.now()
        video.evaluation_data = evaluation_data
        video.trainer_comment = "\n".join(feedback)
        video.save()

        # Cleanup
        cap.release()
        pose.close()

        logger.info(f"Video {video_id} processed successfully")
        return True

    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}")
        video.status = 'failed'
        video.error_message = str(e)
        video.save()
        raise

def generate_exercise_feedback(exercise_type, reps_completed, target_reps, avg_form_score, form_scores):
    """Generate automated feedback based on exercise performance"""
    feedback_parts = []
    
    # Completion feedback
    completion_percentage = (reps_completed / target_reps * 100) if target_reps > 0 else 0
    feedback_parts.append(f"You completed {reps_completed} out of {target_reps} repetitions.")
    
    # Form quality feedback
    if avg_form_score >= 90:
        feedback_parts.append("Your form was excellent throughout the exercise!")
    elif avg_form_score >= 75:
        feedback_parts.append("You maintained good form overall, with some room for improvement.")
    else:
        feedback_parts.append("Focus on maintaining proper form throughout the exercise.")

    # Exercise-specific feedback
    if exercise_type == 'pushup':
        if min(form_scores) < 70:
            feedback_parts.append("Keep your body straight and elbows close to your body during pushups.")
    elif exercise_type == 'squat':
        if min(form_scores) < 70:
            feedback_parts.append("Focus on keeping your knees aligned with your toes and maintain proper depth.")
    elif exercise_type == 'burpee':
        if min(form_scores) < 70:
            feedback_parts.append("Ensure smooth transitions between positions and maintain proper plank form.")
    elif exercise_type == 'lunge':
        if min(form_scores) < 70:
            feedback_parts.append("Keep your front knee aligned and maintain balance throughout the movement.")
    elif exercise_type == 'sprint':
        if avg_form_score < 80:
            feedback_parts.append("Focus on proper arm movement and knee drive for better running efficiency.")
    elif exercise_type == 'jump':
        if avg_form_score < 80:
            feedback_parts.append("Land softly with proper knee alignment and maintain balance.")

    # Progress encouragement
    if completion_percentage >= 100:
        feedback_parts.append("Great job completing all repetitions! Keep up the excellent work! 💪")
    elif completion_percentage >= 75:
        feedback_parts.append("Good effort! You're making progress. Keep pushing to reach your targets! 💪")
    else:
        feedback_parts.append("Keep practicing to build strength and endurance. You've got this! 💪")

    return " ".join(feedback_parts)

def analyze_exercise(exercise_type, landmarks, prev_landmarks, current_stage):
    """
    Analyze form for specific exercises
    Returns: (form_score, rep_completed, new_stage)
    """
    if exercise_type == 'pushup':
        return analyze_pushup(landmarks, current_stage)
    elif exercise_type == 'squat':
        return analyze_squat(landmarks, current_stage)
    elif exercise_type == 'jump':
        return analyze_jump(landmarks, prev_landmarks)
    elif exercise_type == 'sprint':
        return analyze_sprint(landmarks, prev_landmarks)
    elif exercise_type == 'burpee':
        return analyze_burpee(landmarks, current_stage)
    elif exercise_type == 'lunge':
        return analyze_lunge(landmarks, current_stage)
    else:
        return analyze_general_movement(landmarks, prev_landmarks)

def analyze_pushup(landmarks, current_stage):
    """Analyze pushup form"""
    # Get relevant landmarks
    shoulder = landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
    elbow = landmarks[mp.solutions.pose.PoseLandmark.LEFT_ELBOW]
    wrist = landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST]
    hip = landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP]

    # Calculate angle between arm and body
    arm_angle = calculate_angle(shoulder, elbow, wrist)
    body_angle = calculate_angle(shoulder, hip, landmarks[mp.solutions.pose.PoseLandmark.LEFT_KNEE])

    # Determine pushup stage
    rep_completed = False
    if arm_angle > 160 and current_stage != 'up':
        current_stage = 'up'
        rep_completed = True
    elif arm_angle < 90:
        current_stage = 'down'

    # Calculate form score (0-100)
    form_score = 100
    # Deduct points for improper form
    if body_angle < 160:  # body not straight
        form_score -= 20
    if arm_angle < 80:  # too deep
        form_score -= 10

    return form_score, rep_completed, current_stage

def analyze_squat(landmarks, current_stage):
    """Analyze squat form"""
    hip = landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP]
    knee = landmarks[mp.solutions.pose.PoseLandmark.LEFT_KNEE]
    ankle = landmarks[mp.solutions.pose.PoseLandmark.LEFT_ANKLE]
    
    # Calculate knee angle
    knee_angle = calculate_angle(hip, knee, ankle)
    
    rep_completed = False
    if knee_angle > 160 and current_stage != 'up':
        current_stage = 'up'
        rep_completed = True
    elif knee_angle < 90:
        current_stage = 'down'

    # Form scoring
    form_score = 100
    if knee_angle < 70:  # too deep
        form_score -= 15
    if knee.x < ankle.x:  # knee over toes
        form_score -= 20

    return form_score, rep_completed, current_stage

def analyze_jump(landmarks, prev_landmarks):
    """Analyze jump form"""
    if not prev_landmarks:
        return 100, False, None

    hip = landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP]
    prev_hip = prev_landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP]
    
    # Detect jump by vertical movement
    vertical_movement = prev_hip.y - hip.y
    rep_completed = vertical_movement > 0.15  # Threshold for jump detection
    
    form_score = 100
    # Check landing form
    if rep_completed:
        knee = landmarks[mp.solutions.pose.PoseLandmark.LEFT_KNEE]
        ankle = landmarks[mp.solutions.pose.PoseLandmark.LEFT_ANKLE]
        if knee.x < ankle.x:  # knee position on landing
            form_score -= 20

    return form_score, rep_completed, None

def analyze_sprint(landmarks, prev_landmarks):
    """Analyze sprint form"""
    if not prev_landmarks:
        return 100, False, None

    # Calculate knee drive and arm movement
    knee_height = landmarks[mp.solutions.pose.PoseLandmark.LEFT_KNEE].y
    hip_height = landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP].y
    
    form_score = 100
    knee_drive_score = min(100, (hip_height - knee_height) * 200)
    form_score = knee_drive_score

    # Detect stride completion
    stride_completed = False
    if prev_landmarks:
        prev_knee = prev_landmarks[mp.solutions.pose.PoseLandmark.LEFT_KNEE]
        current_knee = landmarks[mp.solutions.pose.PoseLandmark.LEFT_KNEE]
        stride_completed = (prev_knee.y > current_knee.y) and (knee_height < hip_height)

    return form_score, stride_completed, None

def analyze_burpee(landmarks, current_stage):
    """Analyze burpee form"""
    hip = landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP]
    shoulder = landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
    ankle = landmarks[mp.solutions.pose.PoseLandmark.LEFT_ANKLE]

    # Calculate vertical positions
    hip_height = hip.y
    shoulder_height = shoulder.y
    
    form_score = 100
    rep_completed = False

    # State machine for burpee stages
    if current_stage == None or current_stage == 'up':
        if hip_height > 0.7:  # Person is low (in plank or pushup position)
            current_stage = 'down'
    elif current_stage == 'down':
        if hip_height < 0.3:  # Person has jumped up
            current_stage = 'up'
            rep_completed = True
            
    # Form scoring
    if shoulder_height > hip_height:  # Poor plank position
        form_score -= 20

    return form_score, rep_completed, current_stage

def analyze_lunge(landmarks, current_stage):
    """Analyze lunge form"""
    left_knee = landmarks[mp.solutions.pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_KNEE]
    left_ankle = landmarks[mp.solutions.pose.PoseLandmark.LEFT_ANKLE]
    right_ankle = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_ANKLE]

    # Calculate knee angles
    left_knee_angle = calculate_angle(
        landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP],
        left_knee,
        left_ankle
    )
    
    form_score = 100
    rep_completed = False

    if current_stage == None or current_stage == 'up':
        if left_knee_angle < 90:  # In lunge position
            current_stage = 'down'
    elif current_stage == 'down':
        if left_knee_angle > 160:  # Back to standing
            current_stage = 'up'
            rep_completed = True

    # Form scoring
    if abs(left_knee.x - left_ankle.x) > 0.1:  # Knee alignment
        form_score -= 20

    return form_score, rep_completed, current_stage

def analyze_general_movement(landmarks, prev_landmarks):
    """Analyze general movement patterns"""
    if not prev_landmarks:
        return 100, False, None

    # Calculate overall movement intensity
    movement = sum(
        abs(landmarks[i].y - prev_landmarks[i].y)
        for i in range(33)  # MediaPipe provides 33 landmarks
    )
    
    form_score = 100
    significant_movement = movement > 0.1

    return form_score, significant_movement, None

def calculate_angle(point1, point2, point3):
    """Calculate angle between three points"""
    a = np.array([point1.x, point1.y])
    b = np.array([point2.x, point2.y])
    c = np.array([point3.x, point3.y])
    
    ba = a - b
    bc = c - b
    
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)

    return np.degrees(angle)

def add_exercise_overlay(frame, exercise_type, rep_count, form_score, stage, target_reps):
    """Add exercise information overlay to frame"""
    # Background for text
    cv2.rectangle(frame, (10, 10), (300, 130), (0, 0, 0), -1)
    
    # Exercise info
    cv2.putText(frame, f"Exercise: {exercise_type.title()}", (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Reps: {rep_count}/{target_reps}", (15, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Form Score: {form_score:.1f}%", (15, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    if stage:
        cv2.putText(frame, f"Stage: {stage.title()}", (15, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

def get_video_status(request, video_id):
    """Check the processing status of an uploaded video"""
    try:
        video = get_object_or_404(PlayerVideo, id=video_id)
        
        response_data = {
            'status': video.status,
            'progress': getattr(video, 'processing_progress', 0)
        }
        
        if video.status == 'completed':
            response_data.update({
                'trainer_comment': video.trainer_comment,
                'evaluation_data': video.evaluation_data,
                'processed_video_url': video.processed_video.url if video.processed_video else None
            })
            
            # Ensure trainer_comment is not None
            if response_data['trainer_comment'] is None:
                response_data['trainer_comment'] = 'No feedback available yet.'
                
        elif video.status == 'failed':
            response_data['error_message'] = video.error_message
            
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def get_image_embedding(image_path):
    try:
        # Load model with latest weights
        weights = ResNet50_Weights.DEFAULT
        model = resnet50(weights=weights)
        model.eval()
        
        # Remove the last classification layer
        model = torch.nn.Sequential(*list(model.children())[:-1])
        
        # Image preprocessing using the model's transforms
        preprocess = weights.transforms()
        
        # Load and transform image
        img = Image.open(image_path).convert('RGB')
        img_tensor = preprocess(img).unsqueeze(0)  # Add batch dimension
        
        # Get embedding
        with torch.no_grad():
            embedding = model(img_tensor)
            
        return embedding.squeeze().numpy()
        
    except Exception as e:
        print(f"Error in get_image_embedding: {str(e)}")
        raise

@require_http_methods(["POST"])
def visual_search(request):
    if 'image' not in request.FILES:
        return JsonResponse({'error': 'No image provided'}, status=400)
    
    # Save uploaded image temporarily
    image = request.FILES['image']
    temp_path = default_storage.save('temp/search.jpg', ContentFile(image.read()))
    temp_full_path = os.path.join(settings.MEDIA_ROOT, temp_path)
    
    try:
        # Get embedding for uploaded image
        query_embedding = get_image_embedding(temp_full_path)
        
        # Find similar items
        similar_items = []
        embeddings = ItemVisualEmbedding.objects.all()
        
        # Debug print
        print(f"Found {embeddings.count()} items with embeddings")
        
        for embedding in embeddings:
            try:
                item_embedding = embedding.get_embedding_array()
                similarity = 1 - cosine(query_embedding, item_embedding)
                
                # Debug print
                print(f"Item: {embedding.item.name}, Similarity: {similarity}")
                
                # Lower the threshold to see more results
                if similarity > 0.5:  # Changed from 0.7 to 0.5
                    similar_items.append({
                        'id': embedding.item.id,
                        'name': embedding.item.name,
                        'category_id': embedding.item.category.id,
                        'price': str(embedding.item.price),
                        'main_image': embedding.item.main_image.url if embedding.item.main_image else '',
                        'similarity': float(similarity)
                    })
            except Exception as e:
                print(f"Error processing item {embedding.item.name}: {str(e)}")
                continue
        
        # Sort by similarity
        similar_items.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Debug print
        print(f"Found {len(similar_items)} similar items")
        
        return JsonResponse({'items': similar_items[:6]})  # Return top 6 matches
        
    except Exception as e:
        print(f"Error in visual search: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        # Clean up temporary file
        if os.path.exists(temp_full_path):
            default_storage.delete(temp_path)

def generate_embeddings(request):
    """Admin view to generate embeddings for all items"""
    if request.method == 'POST':
        try:
            items = Item.objects.filter(
                main_image__isnull=False  # Only items with images
            ).exclude(
                visual_embedding__isnull=False  # Exclude items that already have embeddings
            )
            
            processed = 0
            errors = 0
            
            for item in items:
                try:
                    # Generate embedding for the item's main image
                    embedding = get_image_embedding(item.main_image.path)
                    
                    # Create new embedding record
                    visual_embedding = ItemVisualEmbedding(item=item)
                    visual_embedding.set_embedding_array(embedding)
                    visual_embedding.save()
                    
                    processed += 1
                    print(f"Successfully processed {item.name}")
                    
                except Exception as e:
                    errors += 1
                    print(f"Error processing {item.name}: {e}")
            
            messages.success(request, f'Successfully processed {processed} items. {errors} errors.')
            
        except Exception as e:
            messages.error(request, f'Error generating embeddings: {str(e)}')
        
        return redirect('admin_dashboard')
        
    return redirect('admin_dashboard')

def check_embedding_status(request):
    """Check the status of embedding generation"""
    total_items = Item.objects.filter(main_image__isnull=False).count()
    items_with_embeddings = ItemVisualEmbedding.objects.count()
    
    return JsonResponse({
        'total_items': total_items,
        'items_with_embeddings': items_with_embeddings,
        'completion_percentage': (items_with_embeddings/total_items*100) if total_items > 0 else 0
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from .models import Users
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
from django.utils.timezone import make_aware, get_current_timezone
from datetime import datetime
import pytz
from django.utils import timezone
import http
from .models import Match



logger = logging.getLogger(__name__)




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

    return render(request, 'player_view.html', {'players_by_position': players_by_position})


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

def stadium(request):
    if request.method == 'POST':
        return store_ticket_data(request)

    # Fetch Real Madrid's matches
    api_key = 'dc93cd61f7a04a67be5652fc72195459'
    url = 'https://api.football-data.org/v4/teams/86/matches'  # Real Madrid's ID is 86
    headers = {'X-Auth-Token': api_key}

    response = requests.get(url, headers=headers)
    all_fixtures = response.json().get('matches', [])

    # Convert UTC dates to IST and filter for upcoming home games
    ist_timezone = pytz.timezone('Asia/Kolkata')
    current_time = timezone.now()
    upcoming_home_fixture = None

    for fixture in all_fixtures:
        utc_date = parse_datetime(fixture['utcDate'])
        if utc_date and fixture['homeTeam']['name'] == 'Real Madrid CF':
            # Make the datetime aware if it's naive
            if utc_date.tzinfo is None:
                utc_date = make_aware(utc_date)
            
            # Only process if the fixture is in the future
            if utc_date > current_time:
                # Convert to IST
                ist_date = utc_date.astimezone(ist_timezone)
                # Format the date as a string
                fixture['ist_date'] = ist_date.strftime("%a, %b %d, %Y, %I:%M %p IST")
                upcoming_home_fixture = fixture
                break  # Stop after finding the first upcoming home match

    if not upcoming_home_fixture:
        return render(request, 'stadium.html', {'error': 'No upcoming home matches found.'})

    # Extract relevant information from the upcoming_home_fixture
    match_info = {
        'id': upcoming_home_fixture['id'],
        'home_team': upcoming_home_fixture['homeTeam']['name'],
        'away_team': upcoming_home_fixture['awayTeam']['name'],
        'competition': upcoming_home_fixture['competition']['name'],
        'match_day': upcoming_home_fixture['matchday'],
        'kickoff_time': upcoming_home_fixture['ist_date'],
    }

    # Fetch all stands with their related sections
    stands = Stand.objects.prefetch_related('sections').all()

    # Create a dictionary to store stands and their sections
    stands_sections = {}
    for stand in stands:
        stands_sections[stand] = stand.sections.all()
    
    # Pass the match details, stands, and sections to the template
    context = {
        'match': match_info,
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
        if utc_date and fixture['homeTeam']['name'] == 'Real Madrid CF':
            if utc_date.tzinfo is None:
                utc_date = make_aware(utc_date)
            
            if utc_date > current_time:
                ist_date = utc_date.astimezone(ist_timezone)
                
                # Create or update the Match object in the database
                Match.objects.update_or_create(
                    match_id=fixture['id'],
                    defaults={
                        'home_team': fixture['homeTeam']['name'],
                        'away_team': fixture['awayTeam']['name'],
                        'utc_date': utc_date,
                        'ist_date': ist_date,
                        'competition': fixture['competition']['name'],
                        'status': fixture['status'],
                        'venue': fixture.get('venue'),
                    }
                )

    # Fetch upcoming home fixtures from the database
    upcoming_home_fixtures = Match.objects.filter(
        home_team='Real Madrid CF',
        utc_date__gt=current_time
    ).order_by('utc_date')

    context = {
        'fixtures': upcoming_home_fixtures,
        'user_name': request.user.username if request.user.is_authenticated else None,
    }
    return render(request, 'schedule.html', context)



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









from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware
import requests
from .models import Users
import pytz

def ticket_checkout(request):
    user_id = request.session.get('user_id')
    user_email = None

    if user_id:
        try:
            user = Users.objects.get(id=user_id)
            user_email = user.email
        except Users.DoesNotExist:
            pass

    ticket_data = request.session.get('ticket_data', {})
    
    if not ticket_data:
        messages.error(request, "No ticket data found. Please select a ticket first.")
        return redirect('stadium')

    match_id = ticket_data.get('match_id')
    match_details = None
    if match_id:
        api_key = 'dc93cd61f7a04a67be5652fc72195459'
        url = f'https://api.football-data.org/v4/matches/{match_id}'
        headers = {'X-Auth-Token': api_key}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            match_data = response.json()
            utc_date = parse_datetime(match_data.get('utcDate', ''))
            
            if utc_date:
                # Convert to IST
                ist_timezone = pytz.timezone('Asia/Kolkata')
                ist_date = utc_date.astimezone(ist_timezone)
                
                match_details = {
                    'home_team': match_data['homeTeam']['name'],
                    'away_team': match_data['awayTeam']['name'],
                    'date': ist_date.strftime('%d %b %Y'),
                    'time': ist_date.strftime('%I:%M %p'),  # 12-hour format with AM/PM
                    'venue': match_data.get('venue', 'Venue not available'),
                    'competition': match_data['competition']['name'],
                }
            else:
                match_details = {
                    'home_team': match_data['homeTeam']['name'],
                    'away_team': match_data['awayTeam']['name'],
                    'date': 'Date not available',
                    'time': 'Time not available',
                    'venue': match_data.get('venue', 'Venue not available'),
                    'competition': match_data['competition']['name'],
                }

            request.session['match_details'] = match_details
            request.session.modified = True

    if not match_details:
        match_details = request.session.get('match_details')

    context = {
        'ticket_data': ticket_data,
        'match_details': match_details,
        'user_id': user_id,
        'user_email': user_email,
    }
    return render(request, 'ticket_checkout.html', context)



    
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
                        full_name=details.get('fullname'),
                        email=details.get('email'),
                        phone=details.get('phone'),
                        address=details.get('address'),
                        apartment=details.get('apartment'),
                        country=details.get('country'),
                        state=details.get('state'),
                        city=details.get('city'),
                        zipcode=details.get('zipcode'),
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
                    'image': item.item.main_image.url if item.item.main_image else None,
                }
                for item in cart_items
            ],
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

@never_cache
def admin_dashboard(request):
    return render (request,'admin_dashboard.html')

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

@never_cache
def admin_add_player(request):
    positions = Position.objects.all()
    return render(request, 'admin_add_player.html', {'position_list': positions})

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


from django.db.models import Q


def store(request):
    # Fetch all categories
    categories = Category.objects.all()

    # Get the search query
    query = request.GET.get('q')

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

    if query:
        # If there's a search query, filter items based on the query
        items = items.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__category_name__icontains=query) |
            Q(subcategory__sub_category_name__icontains=query)
        )
    elif selected_subcategory_id:
        # If a subcategory is selected, filter items based on the subcategory
        items = items.filter(subcategory_id=selected_subcategory_id)
    elif current_category:
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
        'query': query,  # Add the search query to the context
    }

    return render(request, 'store.html', context)



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
            # Standard authentication for other users
            user = Users.objects.get(email=email)
            if check_password(password, user.password):  # Check hashed password
                # Initialize session variables
                request.session['user_id'] = user.id
                request.session['user_name'] = user.name  # Optionally store user's name
                request.session.save()

                # Redirect to a different page after successful login
                return redirect('index')  # Redirect to 'index' page

            else:
                # Unique error message for incorrect credentials
                messages.error(request, "Invalid email or password.", extra_tags='login_error')
                
        except Users.DoesNotExist:
            # Unique error message for non-existent user
            messages.error(request, "Invalid email or password.", extra_tags='login_error')

    return render(request, 'login.html')


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


from django.conf import settings

from django.conf import settings
import requests

import requests
from django.shortcuts import render
from django.conf import settings
import logging


import requests
from django.shortcuts import render
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def previous_results(request):
    url = "https://v3.football.api-sports.io/fixtures"
    
    primary_headers = {
        'x-apisports-key': settings.API_FOOTBALL_KEY
    }
    secondary_headers = {
        'x-apisports-key': '4d6bbab217dd9bdaf14a4203e9313bf1'
    }

    params = {
        'team': 541,  # Real Madrid's team ID
        'last': 10,   # Last 10 matches
        'status': 'FT'  # Only finished matches
    }

    matches = []
    api_source = None

    def fetch_data(headers):
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    try:
        # Try primary API first
        logger.info("Attempting to fetch data from primary API")
        data = fetch_data(primary_headers)

        if 'response' in data and data['response']:
            matches = data['response']
            api_source = 'primary'
            logger.info(f"Fetched {len(matches)} matches from primary API")
        else:
            raise ValueError("No fixtures found in the primary API response")

    except (requests.RequestException, ValueError) as e:
        logger.warning(f"Primary API request failed: {str(e)}. Trying secondary API.")
        
        try:
            # Try secondary API
            logger.info("Attempting to fetch data from secondary API")
            data = fetch_data(secondary_headers)

            if 'response' in data and data['response']:
                matches = data['response']
                api_source = 'secondary'
                logger.info(f"Fetched {len(matches)} matches from secondary API")
            else:
                logger.error("No fixtures found in the secondary API response")

        except requests.RequestException as e:
            logger.error(f"Secondary API request failed: {str(e)}")

    context = {
        'matches': matches,
        'api_source': api_source,
        'api_football_key': settings.API_FOOTBALL_KEY,
    }

    return render(request, 'previous_results.html', context)

def generate_fallback_fixture_ids():
    # Generate some dummy fixture IDs
    return list(range(1000, 1010))  # Returns [1000, 1001, ..., 1009]





def match_details(request, fixture_id):
    api_key = settings.API_FOOTBALL_KEY
    context = {
        'fixture_id': fixture_id,
        'api_football_key': api_key,
    }
    return render(request, 'match_details.html', context)
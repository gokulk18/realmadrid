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
from django.core.paginator import Paginator
from .models import Category
from .models import SubCategory,ItemImage,Item,ItemSize
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
    cart_items = CartItem.objects.filter(cart=cart)
    
    items_data = []
    for cart_item in cart_items:
        items_data.append({
            'id': cart_item.id,
            'name': cart_item.item.name,
            'price': float(cart_item.item.price),
            'quantity': cart_item.quantity,
            'size': cart_item.size,
            'image': cart_item.item.main_image.url if cart_item.item.main_image else '',
            'total': float(cart_item.item.price * cart_item.quantity)
        })
    
    return JsonResponse(items_data, safe=False)




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
        
        if new_quantity <= 0:
            logger.info(f"Removing item from cart. Cart ID: {cart.id}, CartItem ID: {cart_item_id}")
            cart_item.delete()
            return JsonResponse({'success': True, 'message': 'Item removed from cart'})
        
        # Check if the new quantity exceeds available stock
        if cart_item.size:
            item_size = ItemSize.objects.filter(item=cart_item.item, size=cart_item.size).first()
            if item_size:
                available_quantity = item_size.quantity
            else:
                logger.error(f"ItemSize not found for item {cart_item.item.id} and size {cart_item.size}")
                return JsonResponse({'success': False, 'error': 'Item size not available'}, status=400)
        else:
            # If size is not specified, use the total quantity of the item
            available_quantity = sum(size.quantity for size in cart_item.item.sizes.all())

        if new_quantity > available_quantity:
            logger.error(f"Requested quantity exceeds available stock. CartItem ID: {cart_item_id}")
            return JsonResponse({'success': False, 'error': 'Not enough stock available'}, status=400)
        
        cart_item.quantity = new_quantity
        cart_item.save()
        
        logger.info(f"Updated cart item quantity. Cart ID: {cart.id}, CartItem ID: {cart_item_id}, New quantity: {new_quantity}")
        return JsonResponse({'success': True, 'message': 'Cart updated successfully', 'new_quantity': new_quantity})
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








def admin_edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    categories = Category.objects.all()
    subcategories = SubCategory.objects.filter(category=item.category)  # Filter subcategories based on the item's category

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

def stadium_structure(request):
    return render (request,'stadium_structure.html') 



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


def previous_results(request):
    api_key = 'dc93cd61f7a04a67be5652fc72195459'
    url = 'https://api.football-data.org/v4/teams/86/matches'  # Real Madrid's ID is 86
    headers = {'X-Auth-Token': api_key}

    response = requests.get(url, headers=headers)
    fixtures = response.json().get('matches', [])

    # Convert UTC dates to IST and filter for completed matches
    ist_timezone = pytz.timezone('Asia/Kolkata')
    results = []
    
    for fixture in fixtures:
        # We only want completed matches
        if fixture['status'] == 'FINISHED':
            utc_date = parse_datetime(fixture['utcDate'])
            if utc_date:
                if utc_date.tzinfo is None:
                    utc_date = make_aware(utc_date)
                ist_date = utc_date.astimezone(ist_timezone)
                formatted_date = ist_date.strftime("%a, %b %d, %Y, %I:%M %p IST")
            else:
                formatted_date = "Date not available"

            match_result = {
                'date': formatted_date,
                'home_team': fixture['homeTeam']['name'],
                'away_team': fixture['awayTeam']['name'],
                'home_score': fixture['score']['fullTime']['home'],
                'away_score': fixture['score']['fullTime']['away'],
                'competition': fixture['competition']['name'],
                'matchday': fixture.get('matchday', 'N/A'),
            }
            results.append(match_result)

    # Add results to the context
    context = {
        'real_madrid_results': results,
    }

    # Render the results in a template (assuming you have a template named 'previous_results.html')
    return render(request, 'previous_results.html', context)

def match_details(request, match_id):
    api_key = 'YOUR_API_KEY'
    url = f'https://api.football-data.org/v4/matches/{match_id}'
    headers = {'X-Auth-Token': api_key}

    response = requests.get(url, headers=headers)
    match_data = response.json()

    # Extract home and away stats
    home_stats = match_data.get('homeTeam', {}).get('statistics', {})
    away_stats = match_data.get('awayTeam', {}).get('statistics', {})

    # Extract goal scorers
    goal_scorers = []
    for goal in match_data.get('goals', []):
        scorer = {
            'name': goal['scorer']['name'],
            'minute': goal['minute'],
            'team': 'home' if goal['team']['id'] == match_data['homeTeam']['id'] else 'away'
        }
        goal_scorers.append(scorer)

    match_info = {
        'date': formatted_date,
        'competition': match_data['competition']['name'],
        'home_team': match_data['homeTeam']['name'],
        'away_team': match_data['awayTeam']['name'],
        'home_score': match_data['score']['fullTime']['home'],
        'away_score': match_data['score']['fullTime']['away'],
        'home_stats': {
            'possession': home_stats.get('ballPossession', 'N/A'),
            'shots': home_stats.get('shots', 'N/A'),
            'shots_on_target': home_stats.get('shotsOnGoal', 'N/A'),
            'fouls': home_stats.get('fouls', 'N/A'),
            'offsides': home_stats.get('offsides', 'N/A'),
            'yellow_cards': home_stats.get('yellowCards', 'N/A'),
            'red_cards': home_stats.get('redCards', 'N/A'),
        },
        'away_stats': {
            'possession': away_stats.get('ballPossession', 'N/A'),
            'shots': away_stats.get('shots', 'N/A'),
            'shots_on_target': away_stats.get('shotsOnGoal', 'N/A'),
            'fouls': away_stats.get('fouls', 'N/A'),
            'offsides': away_stats.get('offsides', 'N/A'),
            'yellow_cards': away_stats.get('yellowCards', 'N/A'),
            'red_cards': away_stats.get('redCards', 'N/A'),
        },
        'goal_scorers': goal_scorers,
    }

    return render(request, 'match_details.html', {'match_info': match_info})
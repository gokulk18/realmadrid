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



logger = logging.getLogger(__name__)



class CustomTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(timestamp)

token_generator = CustomTokenGenerator()

def add_position(request):
    if request.method == 'POST':
        position_name = request.POST.get('position')
        if position_name:
            Position.objects.create(position=position_name)
            messages.success(request, 'Position added successfully!')
            return redirect('admin_add_player')  # Redirect to the page where you want to show the message
    return render(request, 'admin_add_player.html')

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
        messages.success(request, 'Player added successfully!')
        return redirect('admin_add_player')  # Redirect to the page where you want to show the message

    return render(request, 'add_player.html')

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

@never_cache
def admin_add_player(request):
    positions = Position.objects.all()
    return render(request, 'admin_add_player.html', {'position_list': positions})

@never_cache
def admin_squad_list(request):
    # Fetch all positions
    positions = Position.objects.all()

    # Create a dictionary to hold players by position
    players_by_position = {}
    for position in positions:
        players_by_position[position.position] = Player.objects.filter(player_position=position)

    return render(request, 'admin_squad_list.html', {'players_by_position': players_by_position})





@never_cache
def index(request):
    if 'user_id' in request.session:
        user_id = request.session['user_id']
        try:
            # Retrieve user object from database
            user = Users.objects.get(id=user_id)
            context = {
                'user_name': user.name,  # Assuming 'name' is the field you want to display
                'user_email': user.email,
                'user_phone': user.phone,
            }
            return render(request, 'index.html', context)
        except Users.DoesNotExist:
            # Handle case where user_id in session does not match any user in the database
            return render(request, 'index.html', {'user_name': None})
    else:
        # User is not authenticated, redirect to login page or handle as needed
        return render(request, 'index.html', {'user_name': None})
    
def generate_otp():
    return random.randint(1000, 9999)

def position_list(request):
    positions = Position.objects.all()
    return render(request, 'admin_add_player.html', {'position_list': positions})

@never_cache
def profile(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        user_id = request.session.get('user_id')
        try:
            user = Users.objects.get(id=user_id)
            user.name = name
            user.phone = phone
            user.save()
            messages.success(request, 'Profile updated successfully.')
            # Render the profile page with the success message
            context = {
                'user_name': user.name,
                'user_email': user.email,
                'user_phone': user.phone,
            }
            return render(request, 'profile.html', context)
        except Users.DoesNotExist:
            messages.error(request, 'User not found.')
            return render(request, 'profile.html')
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
            return render(request, 'profile.html')

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
            return redirect('admin_dashboard')  # Replace 'admin_dashboard' with your URL name

        try:
            # Standard authentication for other users
            user = Users.objects.get(email=email)
            if check_password(password, user.password):  # Check hashed password
                # Initialize session variables
                request.session['user_id'] = user.id
                request.session['user_name'] = user.name  # Optionally store user's name
                request.session.save()

                # Redirect to a different page after successful login
                return redirect('index')  # Replace 'index' with your desired URL name

            else:
                messages.error(request, "Invalid email or password.")

        except Users.DoesNotExist:
            messages.error(request, "Invalid email or password.")

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
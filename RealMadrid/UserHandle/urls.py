from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf.urls.static import static  # Import static
from django.conf import settings

urlpatterns = [
    path('', views.index, name="index"),
    path('register', views.register, name="register"),
    path('login', views.login, name="login"),
    path('stadium_structure',views.stadium_structure,name="stadium_structure"),
    path('email_otp_verif', views.email_otp_verif, name="email_otp_verif"),
    path('profile',views.profile,name="profile"),
    path('logout',views.logout,name="logout"),
    path('password_reset/', views.forgotpassword, name="forgotpassword"),
    path('reset/<uidb64>/<token>/', views.password_reset, name="password_reset"),
    path('accounts/', include('allauth.urls')),
    path('check_email_availability/', views.check_email_availability, name="check_email_availability"),
    path('admin_dashboard/',views.admin_dashboard,name="admin_dashboard"),
    path('admin_squad_list/',views.admin_squad_list,name="admin_squad_list"),
    path('admin_add_player/',views.admin_add_player,name="admin_add_player"),
    path('add_position/', views.add_position, name='add_position'),
    path('add_player/', views.add_player, name='add_player'),
    path('admin_update_player/<int:player_id>/', views.admin_update_player, name='admin_update_player'),





    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

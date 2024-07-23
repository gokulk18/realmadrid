from django.contrib import admin
from django.urls import path, include
from . import views

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
]

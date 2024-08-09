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
    path('store/', views.store, name="store"),
    path('product/<int:category_id>/<int:item_id>/', views.product_details, name='product_details'),
    path('view-more-category/<int:category_id>/', views.view_more_category, name='view_more_category'),
    path('category/<int:category_id>/product/<int:item_id>/', views.product_single_view, name='product_single_view'),


    path('admin_dashboard/',views.admin_dashboard,name="admin_dashboard"),
    path('admin_squad_list/',views.admin_squad_list,name="admin_squad_list"),
    path('admin_add_player/',views.admin_add_player,name="admin_add_player"),
    path('add_position/', views.add_position, name='add_position'),
    path('add_player/', views.add_player, name='add_player'),
    path('admin_update_player/<int:player_id>/', views.admin_update_player, name='admin_update_player'),
    path('admin_show_news/', views.admin_show_news, name='admin_show_news'),
    path('admin_add_news/', views.admin_add_news, name='admin_add_news'),
    path('add_news/', views.add_news, name='add_news'),
    path('news/<int:id>/', views.user_view_news, name='user_view_news'),
    path('admin_view_store/', views.admin_view_store, name='admin_view_store'),
    path('admin_add_category/', views.admin_add_category, name='admin_add_category'),
    path('admin_add_subcategory/', views.admin_add_subcategory, name='admin_add_subcategory'),
    path('admin_add_item/', views.admin_add_item, name='admin_add_item'),
    path('get_subcategories/<int:category_id>/', views.get_subcategories, name='get_subcategories'),









    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

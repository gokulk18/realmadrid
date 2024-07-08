from django.contrib import admin
from .models import Users

class UsersAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'password')
    search_fields = ('name', 'email')

admin.site.register(Users, UsersAdmin)
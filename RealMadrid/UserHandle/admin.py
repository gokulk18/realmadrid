from django.contrib import admin
from .models import Users, Position, Player ,News,Category,SubCategory

class UsersAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'password', 'username')
    search_fields = ('name', 'email')

class PositionAdmin(admin.ModelAdmin):
    list_display = ('id', 'position')
    search_fields = ('position',)

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('jersey_num', 'player_name', 'player_country', 'player_position', 'player_role', 'player_image')
    search_fields = ('player_name', 'player_country', 'player_role')
    list_filter = ('player_position',)

class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'news_image','date_created')
    search_fields = ('title', 'description')
    
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category_name')
    search_fields = ('category_name',)

class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category_name', 'sub_category_name')
    search_fields = ('category__category_name', 'sub_category_name',)

    def category_name(self, obj):
        return obj.category.category_name
    category_name.admin_order_field = 'category'  # Allows column sorting
    category_name.short_description = 'Category Name'  # Column header name
    

# Register the models with the admin site
admin.site.register(Users, UsersAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(News,NewsAdmin)
admin.site.register(Category,CategoryAdmin)
admin.site.register(SubCategory,SubCategoryAdmin)


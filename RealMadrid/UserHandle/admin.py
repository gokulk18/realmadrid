from django.contrib import admin
from .models import (
    Users, Position, Player, News, Category, SubCategory, Item, ItemImage, ItemSize,
    Cart, CartItem, Wishlist, WishlistItem, Order, OrderItem, Payment, Shipping
)

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

class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1

class ItemSizeInline(admin.TabularInline):
    model = ItemSize
    extra = 1

class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'subcategory', 'price', 'total_quantity')
    fields = ('name', 'category', 'subcategory', 'price', 'description', 'main_image')
    inlines = [ItemSizeInline, ItemImageInline]

    def total_quantity(self, obj):
        return sum(size.quantity for size in obj.sizes.all())
    total_quantity.short_description = 'Total Quantity'

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1

class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_name', 'created_at', 'updated_at')
    inlines = [CartItemInline]
    search_fields = ('user__name',)

    def user_name(self, obj):
        return obj.user.name
    user_name.admin_order_field = 'user__name'
    user_name.short_description = 'User Name'

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart_user', 'item', 'quantity', 'size')
    list_filter = ('cart__user', 'item')
    search_fields = ('cart__user__name', 'item__name')

    def cart_user(self, obj):
        return obj.cart.user.name
    cart_user.admin_order_field = 'cart__user__name'
    cart_user.short_description = 'User'

class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 1

class WishlistAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_name', 'created_at', 'updated_at')
    inlines = [WishlistItemInline]
    search_fields = ('user__name',)

    def user_name(self, obj):
        return obj.user.name
    user_name.admin_order_field = 'user__name'
    user_name.short_description = 'User Name'

class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'wishlist_user', 'item', 'added_at')
    list_filter = ('wishlist__user', 'item')
    search_fields = ('wishlist__user__name', 'item__name')

    def wishlist_user(self, obj):
        return obj.wishlist.user.name
    wishlist_user.admin_order_field = 'wishlist__user__name'
    wishlist_user.short_description = 'User'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'full_name', 'email', 'phone', 'status', 'total', 'is_paid', 'created_at')
    search_fields = ('order_number', 'full_name', 'email')
    list_filter = ('status', 'is_paid', 'created_at')
    inlines = [OrderItemInline]

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'order', 'payment_method', 'amount_paid', 'status', 'created_at')
    search_fields = ('transaction_id', 'order__order_number')
    list_filter = ('status', 'payment_method', 'created_at')

class ShippingAdmin(admin.ModelAdmin):
    list_display = ('order', 'shipping_method', 'tracking_number', 'status', 'estimated_delivery', 'shipped_at', 'delivered_at')
    search_fields = ('order__order_number', 'tracking_number')
    list_filter = ('status', 'shipping_method', 'shipped_at', 'delivered_at')

# Register the models with the admin site
admin.site.register(Users, UsersAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(News, NewsAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(WishlistItem, WishlistItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Shipping, ShippingAdmin)

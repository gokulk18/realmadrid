from django.contrib import admin
from .models import (
    Users, Position, Player, News, Category, SubCategory, Item, ItemImage, ItemSize,
    Cart, CartItem, Wishlist, WishlistItem, Order, OrderItem, Payment, Shipping,
    Stand, Section, Match, TicketOrder, TicketItem, TicketPayment, QuizQuestion,
    UploadedImage, IdentifyPlayer, PlayerCredentials
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

class SectionInline(admin.TabularInline):
    model = Section
    extra = 1

class SectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'stand', 'seats', 'price')
    list_filter = ('stand',)
    search_fields = ('name', 'stand__name')

    def seats_display(self, obj):
        return ", ".join(obj.seats)
    seats_display.short_description = 'Seats'

class StandAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

class MatchAdmin(admin.ModelAdmin):
    list_display = ('match_id', 'home_team', 'away_team', 'utc_date', 'ist_date', 'competition', 'status', 'venue')
    list_filter = ('competition', 'status', 'home_team', 'away_team')
    search_fields = ('match_id', 'home_team', 'away_team', 'competition')
    date_hierarchy = 'utc_date'
    readonly_fields = ('last_updated',)

    fieldsets = (
        (None, {
            'fields': ('match_id', 'home_team', 'away_team', 'competition', 'status')
        }),
        ('Date and Time', {
            'fields': ('utc_date', 'ist_date')
        }),
        ('Additional Info', {
            'fields': ('venue', 'last_updated')
        }),
    )

class TicketItemInline(admin.TabularInline):
    model = TicketItem
    extra = 1

class TicketOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'full_name', 'email', 'phone', 'match', 'total_price', 'status', 'is_paid', 'created_at')
    search_fields = ('order_number', 'full_name', 'email')
    list_filter = ('status', 'is_paid', 'match')
    inlines = [TicketItemInline]
    readonly_fields = ('order_number',)

class TicketItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'stand', 'section', 'seat_number', 'price')
    list_filter = ('stand', 'section')
    search_fields = ('order__order_number', 'order__full_name')

class TicketPaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'ticket_order', 'payment_method', 'amount_paid', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('transaction_id', 'ticket_order__order_number', 'ticket_order__full_name')
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('ticket_order', 'transaction_id', 'payment_method', 'amount_paid', 'status')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('ticket_order', 'transaction_id')
        return self.readonly_fields

class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text',)
    search_fields = ('question_text',)

class UploadedImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'uploaded_at')  # Display fields in the admin
    search_fields = ('id',)  # Add search functionality if needed

class IdentifyPlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'image')  # Display fields in the admin
    search_fields = ('name',)  # Add search functionality for the name field

class PlayerCredentialsAdmin(admin.ModelAdmin):
    list_display = ('player', 'email', 'created_at', 'updated_at')
    search_fields = ('player__player_name', 'email')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

# Register the models with the admin site
admin.site.register(Users, UsersAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(PlayerCredentials, PlayerCredentialsAdmin)
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

# Register the new models
admin.site.register(Stand, StandAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(TicketOrder, TicketOrderAdmin)
admin.site.register(TicketItem, TicketItemAdmin)
admin.site.register(TicketPayment, TicketPaymentAdmin)
admin.site.register(QuizQuestion, QuizQuestionAdmin)
admin.site.register(UploadedImage, UploadedImageAdmin)  # Register the UploadedImage model
admin.site.register(IdentifyPlayer, IdentifyPlayerAdmin)  # Register the IdentifyPlayer model

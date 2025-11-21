from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

from django.contrib import admin
from user.models import (
    Address, Cart, CartItem, Review,
    Wishlist, CustomerProfile, Order, OrderItem
)


# -------------------- INLINE MODELS --------------------
# Allows adding CartItems inside Cart admin
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1


# Allows adding OrderItems inside Order admin
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


# -------------------- MODEL ADMINS --------------------
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'customer', 'city', 'is_default')
    list_filter = ('city', 'state', 'is_default')
    search_fields = ('full_name', 'city', 'state', 'customer__username')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('customer', 'created_at')
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')
    list_filter = ('product',)
    search_fields = ('product__name',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('customer', 'product', 'rating', 'created_at', 'is_verified_purchase')
    list_filter = ('rating', 'is_verified_purchase')
    search_fields = ('customer__username', 'product__name')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('customer', 'product', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('customer__username', 'product__name')


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')
    search_fields = ('user__username', 'phone')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'customer__username')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'product_sku', 'quantity', 'price')
    list_filter = ('order',)
    search_fields = ('product_name', 'product_sku')

class User(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('seller', 'Seller'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')    
    

    def __str__(self):
        return f"{self.username} ({self.role})"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

from user.models import Order


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('order', 'New Order'),
        ('review', 'New Review'),
        ('system', 'System Update'),
        ('low_stock', 'Low Stock Alert'),
    )
    
    # FIX: Use settings.AUTH_USER_MODEL
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    icon = models.CharField(max_length=50, default='fas fa-bell')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='order')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        # REMOVE this line or Django will auto-generate table name
        # db_table = 'core_notification'
    
    def __str__(self):
        return f"{self.user.username} - {self.message}"
    
    @property
    def time(self):
        return self.created_at.strftime('%H:%M')

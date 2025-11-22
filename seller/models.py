from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from user.models import Order
from core.models import Category
class SellerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller_profile'
    )
    shop_name = models.CharField(max_length=100)
    gst_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.shop_name



class Product(models.Model):
    seller = models.ForeignKey(
        SellerProfile,
        on_delete=models.CASCADE,
        related_name='products'
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    sku = models.CharField(max_length=50, unique=True)

    description = models.TextField()
    brand = models.CharField(max_length=100, blank=True, null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)   # base price
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
    
    # @property
    # def main_image_obj(self):
    #     main_img = self.images.filter(is_main=True).first()
    #     if main_img:
    #         return main_img
    #     return self.images.first()


    


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='products/')
    is_main = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_main:
           
            ProductImage.objects.filter(
                product=self.product,
                is_main=True
            ).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image - {self.product.name}"


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('order', 'New Order'),
        ('review', 'New Review'),
        ('low_stock', 'Low Stock'),
    )
    
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='order')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.seller.username} - {self.message}"
    
    @property
    def time(self):
        return self.created_at.strftime('%H:%M')
    
    @property
    def icon(self):
        """Get appropriate icon based on notification type"""
        icons = {
            'order': 'fas fa-shopping-bag',
            'review': 'fas fa-star',
            'low_stock': 'fas fa-exclamation-triangle',
        }
        return icons.get(self.notification_type, 'fas fa-bell')
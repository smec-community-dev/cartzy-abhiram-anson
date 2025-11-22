from django.db import models
from django.conf import settings



class Address(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'customer'},
        related_name='addresses'
    )
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    street = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default='India')
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.city}"


class Cart(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'customer'}
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def total_amount(self):
        return sum(item.subtotal() for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('seller.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def subtotal(self):
        price = self.product.discount_price or self.product.price
        return price * self.quantity


class Review(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'customer'}
    )
    product = models.ForeignKey('seller.Product', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(
        default=5,
        choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')]
    )
    review_title=models.CharField(max_length=255,null=True)
    review_text =models.CharField(max_length=255,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Add these fields for seller functionality
    seller_reply = models.TextField(blank=True, null=True)
    replied_at = models.DateTimeField(blank=True, null=True)
    is_verified_purchase = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['customer', 'product']  # Prevent multiple reviews from same customer
    
    def _str_(self):
        return f"{self.customer.get_full_name()} - {self.product.name} - {self.rating} Stars"
    
    def get_customer_initials(self):
        return f"{self.customer.first_name[0]}{self.customer.last_name[0]}".upper()
    
    def get_customer_full_name(self):
        return self.customer.get_full_name()
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_reply = None
        if not is_new:
            try:
                old_review = Review.objects.get(pk=self.pk)
                old_reply = old_review.seller_reply
            except Review.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Trigger notification when seller replies to review
        if not is_new and self.seller_reply and self.seller_reply != old_reply:
            from .notification_service import CustomerNotificationTriggers
            CustomerNotificationTriggers.notify_review_reply(
                customer=self.customer,
                review=self,
                seller_reply=self.seller_reply
            )

class ReviewImage(models.Model):
    review = models.ForeignKey(
        'Review',
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='review_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Review {self.review.id}"



class Wishlist(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'customer'}
    )
    product = models.ForeignKey('seller.Product', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('customer', 'product')


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile'
    )
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.user.username


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'customer'}
    )
    address = models.ForeignKey('user.Address', on_delete=models.SET_NULL, null=True)
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_seller_subtotal(self, seller_user):
        """Calculate subtotal for a specific seller in this order"""
        from django.db.models import Sum
        seller_items = self.items.filter(product_seller_user=seller_user)
        return seller_items.aggregate(total=Sum('price'))['total'] or 0
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if self.pk:
            old_order = Order.objects.get(pk=self.pk)
            old_status = old_order.status
            
            super().save(*args, **kwargs)
            
            # Trigger notification when order status changes
            if self.status != old_status:
                from .notification_service import CustomerNotificationTriggers
                CustomerNotificationTriggers.notify_order_status_update(
                    customer=self.customer,
                    order=self,
                    old_status=old_status,
                    new_status=self.status
                )
                
                # Specific notifications for shipped/delivered
                if self.status == 'Shipped':
                    CustomerNotificationTriggers.notify_order_shipped(
                        customer=self.customer,
                        order=self
                    )
                elif self.status == 'Delivered':
                    CustomerNotificationTriggers.notify_order_delivered(
                        customer=self.customer,
                        order=self
                    )
        else:
            super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('seller.Product', on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product_name} - {self.order.order_number}"


class CustomerNotification(models.Model):
    NOTIFICATION_TYPES = (
        ('review_reply', 'Review Reply'),
        ('order_status', 'Order Status Update'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('promotion', 'Special Promotion'),
    )
    
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='order_status')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.username} - {self.message}"
    
    @property
    def time(self):
        return self.created_at.strftime('%H:%M')
    
    @property
    def icon(self):
        """Get appropriate icon based on notification type"""
        icons = {
            'review_reply': 'fas fa-comment',
            'order_status': 'fas fa-shipping-fast',
            'order_shipped': 'fas fa-truck',
            'order_delivered': 'fas fa-check-circle',
            'promotion': 'fas fa-percentage',
        }
        return icons.get(self.notification_type, 'fas fa-bell')
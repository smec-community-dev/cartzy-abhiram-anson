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
    review_title = models.CharField(max_length=255, null=True)
    review_text = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    replied_at = models.DateTimeField(blank=True, null=True)
    is_verified_purchase = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['customer', 'product']
    
    def __str__(self):
        return f"{self.customer.get_full_name()} - {self.product.name} - {self.rating} Stars"
    
    def get_customer_initials(self):
        return f"{self.customer.first_name[0]}{self.customer.last_name[0]}".upper()
    
    def get_customer_full_name(self):
        return self.customer.get_full_name()
    
    # NO save method - use the default one

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


# In user/models.py

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('RAZORPAY', 'Pay Now (Razorpay)'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
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
    
    # Payment Fields
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES, 
        default='COD'
    )
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='PENDING'
    )
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_seller_subtotal(self, seller_user):
        """Calculate subtotal for a specific seller in this order"""
        from django.db.models import Sum
        seller_items = self.items.filter(product__seller__user=seller_user)
        return seller_items.aggregate(total=Sum('price'))['total'] or 0
    
    def get_seller_items(self, seller_user):
        """Get all order items for a specific seller"""
        return self.items.filter(product__seller__user=seller_user)
    
    def has_items_from_seller(self, seller_user):
        """Check if this order has items from the given seller"""
        return self.items.filter(product__seller__user=seller_user).exists()
    
    def is_paid(self):
        """Check if order is paid"""
        return self.payment_status == 'PAID'
    
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in ['Pending', 'Processing'] and self.payment_method == 'COD'
    
    def __str__(self):
        return f"Order #{self.order_number}"
    


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
        ('order_placed', 'Order Placed'),
        ('order_confirmed', 'Order Confirmed'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('order_cancelled', 'Order Cancelled'),
        ('seller_reply', 'Seller Reply'),
        ('promotion', 'Promotion'),
        ('info', 'Information')
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL,   on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
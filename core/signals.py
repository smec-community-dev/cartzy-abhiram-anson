from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from user.models import Order
from .models import Notification  # Import from core

@receiver(post_save, sender=Order)
def create_order_notifications(sender, instance, created, **kwargs):
    if created:
        print(f"📦 Order #{instance.order_number} created, creating seller notifications...")
        
        User = get_user_model()
        seller_users = User.objects.filter(
            seller_profile__product__orderitem__order=instance
        ).distinct()
        
        for seller_user in seller_users:
            seller_items_count = instance.items.filter(
                product__seller__user=seller_user
            ).count()
            
            if seller_items_count > 0:
                Notification.objects.create(
                    user=seller_user,
                    message=f'New order #{instance.order_number} received with {seller_items_count} item(s)',
                    icon='fas fa-shopping-bag',
                    notification_type='order',
                    related_order=instance
                )
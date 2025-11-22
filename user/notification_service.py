from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import CustomerNotification

class CustomerNotificationService:
    
    @staticmethod
    def create_customer_notification(customer, message, notification_type, order=None, review=None):
        """Create customer notification and send real-time update"""
        notification = CustomerNotification.objects.create(
            customer=customer,
            message=message,
            notification_type=notification_type,
            order=order,
            review=review
        )
        
        # Send real-time notification via WebSocket
        CustomerNotificationService.send_real_time_notification(customer, notification)
        
        return notification
    
    @staticmethod
    def send_real_time_notification(customer, notification):
        """Send real-time notification to customer via WebSocket"""
        channel_layer = get_channel_layer()
        
        try:
            async_to_sync(channel_layer.group_send)(
                f'notifications_{customer.id}',
                {
                    'type': 'notification_message',
                    'message': {
                        'id': notification.id,
                        'message': notification.message,
                        'type': notification.notification_type,
                        'icon': notification.icon,
                        'time': notification.time,
                        'is_read': notification.is_read,
                        'order_id': notification.order.id if notification.order else None,
                        'review_id': notification.review.id if notification.review else None
                    }
                }
            )
            print(f"📢 [CUSTOMER WS] Sent real-time notification to customer {customer.username}")
        except Exception as e:
            print(f"❌ [CUSTOMER WS] Error sending real-time notification: {e}")
            
class CustomerNotificationTriggers:
    
    @staticmethod
    def notify_review_reply(customer, review, seller_reply):
        """Notify customer when seller replies to their review"""
        message = f"Seller replied to your review: '{seller_reply}'"
        
        CustomerNotificationService.create_customer_notification(
            customer=customer,
            message=message,
            notification_type='review_reply',
            review=review
        )
        print(f"📝 [CUSTOMER NOTI] Review reply notification sent to {customer.username}")
    
    @staticmethod
    def notify_order_status_update(customer, order, old_status, new_status):
        """Notify customer when order status changes"""
        message = f"Your order #{order.id} status changed from {old_status} to {new_status}"
        
        CustomerNotificationService.create_customer_notification(
            customer=customer,
            message=message,
            notification_type='order_status',
            order=order
        )
        print(f"📦 [CUSTOMER NOTI] Order status update sent to {customer.username}")
    
    @staticmethod
    def notify_order_shipped(customer, order, tracking_number=None):
        """Notify customer when order is shipped"""
        message = f"Your order #{order.id} has been shipped!"
        if tracking_number:
            message += f" Tracking: {tracking_number}"
        
        CustomerNotificationService.create_customer_notification(
            customer=customer,
            message=message,
            notification_type='order_shipped',
            order=order
        )
    
    @staticmethod
    def notify_order_delivered(customer, order):
        """Notify customer when order is delivered"""
        message = f"Your order #{order.id} has been delivered!"
        
        CustomerNotificationService.create_customer_notification(
            customer=customer,
            message=message,
            notification_type='order_delivered',
            order=order
        )
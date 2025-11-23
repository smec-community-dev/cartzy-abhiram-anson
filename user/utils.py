from .models import CustomerNotification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json

def send_user_websocket_notification(user_id, notification):
    """Send notification to user via WebSocket"""
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{user_id}',
            {
                'type': 'send_notification',
                'notification': {
                    'id': notification.id,
                    'title': notification.title,
                    'message': notification.message,
                    'type': notification.notification_type,
                    'created_at': notification.created_at.isoformat(),
                    'is_read': notification.is_read,
                    'order_id': notification.order.id if notification.order else None
                }
            }
        )
        print(f"WebSocket notification sent to user_{user_id}")
    except Exception as e:
        print(f"User WebSocket error: {e}")

def create_seller_reply_notification(seller_reply):
    """Create notification for user when seller replies to their review"""
    try:
        print(f"🔔 Starting notification creation for seller reply #{seller_reply.id}")
        
        review = seller_reply.review
        print(f"📝 Review: {review.id}, Customer: {review.customer}")
        
        user = review.customer  # ✅ Use 'customer' field from Review model
        print(f"👤 User: {user.username} (ID: {user.id})")
        
        seller = seller_reply.seller
        product = review.product
        
        # Create the notification message
        message = f'{seller.user.get_full_name()} replied to your review on {product.name}: "{seller_reply.reply_text[:50]}{"..." if len(seller_reply.reply_text) > 50 else ""}"'
        
        print(f"Creating seller reply notification for user {user.username}")
        
        # Save to database
        notification = CustomerNotification.objects.create(
            user=user,
            title="Seller Replied to Your Review",
            message=message,
            notification_type='seller_reply',
            order=review.order if hasattr(review, 'order') else None
        )
        
        # Send via WebSocket
        send_user_websocket_notification(user.id, notification)
        
        print(f"✅ Seller reply notification created: {message}")
        return notification
        
    except Exception as e:
        print(f"❌ Error creating seller reply notification: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_user_order_notification(order, order_items=None):
    """Create notifications for user when order is placed with PRODUCT NAMES"""
    print(f"[USER NOTIFICATION] Creating notifications for order #{order.order_number}")
    
    try:
        customer = order.customer
        
        # Use provided order_items or get from order
        if order_items is None:
            order_items = order.items.all()
        
        # Create the message with product names
        if len(order_items) == 1:
            message = f'Order placed: {order_items[0].product_name} - ₹{order.total_amount}'
        elif len(order_items) == 2:
            message = f'Order placed: {order_items[0].product_name} & {order_items[1].product_name} - ₹{order.total_amount}'
        else:
            message = f'Order placed: {order_items[0].product_name}, {order_items[1].product_name} + {len(order_items)-2} more - ₹{order.total_amount}'
        
        print(f"Creating user notification: {message}")
        
        # Save to database
        notification = CustomerNotification.objects.create(
            user=customer,
            title="Order Placed",
            message=message,
            notification_type='order_placed',
            order=order
        )
        
        # Send via WebSocket
        send_user_websocket_notification(customer.id, notification)
        
        print(f"User notification created: {message}")
        return notification
        
    except Exception as e:
        print(f"Error creating user notification: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_order_status_notification(order, status):
    """Create notification for user when order status changes"""
    try:
        customer = order.customer
        
        status_messages = {
            'confirmed': f'Order #{order.order_number} has been confirmed',
            'shipped': f'Order #{order.order_number} has been shipped',
            'delivered': f'Order #{order.order_number} has been delivered',
            'cancelled': f'Order #{order.order_number} has been cancelled'
        }
        
        message = status_messages.get(status, f'Order #{order.order_number} status updated to {status}')
        
        notification = CustomerNotification.objects.create(
            user=customer,
            title="Order Status Update",
            message=message,
            notification_type=f'order_{status}',
            order=order
        )
        
        # Send via WebSocket
        send_user_websocket_notification(customer.id, notification)
        
        print(f"Order status notification created: {message}")
        return notification
        
    except Exception as e:
        print(f"Error creating order status notification: {e}")
        return None

def create_promotional_notification(user, title, message):
    """Create promotional notifications for users"""
    try:
        notification = CustomerNotification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type='promotion'
        )
        
        # Send via WebSocket
        send_user_websocket_notification(user.id, notification)
        
        return notification
        
    except Exception as e:
        print(f"Error creating promotional notification: {e}")
        return None
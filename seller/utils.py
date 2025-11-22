from seller.models import Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json

def create_order_notification(order, order_items=None):
    """Create notifications for all sellers in an order with PRODUCT NAMES"""
    print(f"🔔 [PRODUCT NAMES VERSION] Creating notifications for order #{order.order_number}")
    
    # Use provided order_items or get from order
    if order_items is None:
        order_items = order.items.all()
    
    # Group items by seller
    seller_data = {}
    
    for item in order_items:
        try:
            # FIX: Import Product from seller.models instead of user.models
            from seller.models import Product  # ← THIS IS THE FIX!
            product = Product.objects.get(id=item.product_id)
            
            if hasattr(product, 'seller') and product.seller:
                seller = product.seller.user
                if seller not in seller_data:
                    seller_data[seller] = []
                
                seller_data[seller].append({
                    'name': product.name,
                    'quantity': item.quantity,
                    'price': float(item.price)
                })
        except Exception as e:
            print(f"❌ Error processing item: {e}")
    
    # Create notifications for each seller
    for seller, items in seller_data.items():
        try:
            total_amount = sum(item['price'] * item['quantity'] for item in items)
            
            # Create the new message format with product names
            if len(items) == 1:
                message = f'New order: {items[0]["name"]} - ₹{total_amount}'
            elif len(items) == 2:
                message = f'New order: {items[0]["name"]} & {items[1]["name"]} - ₹{total_amount}'
            else:
                message = f'New order: {items[0]["name"]}, {items[1]["name"]} + {len(items)-2} more - ₹{total_amount}'
            
            print(f"Creating notification: {message}")
            
            # Save to database
            notification = Notification.objects.create(
                seller=seller,
                message=message,  # This is the new format!
                notification_type='order',
                order=order
            )
            
            # Send via WebSocket
            send_websocket_notification(seller.id, notification)
            
        except Exception as e:
            print(f"Error creating notification: {e}")

def send_websocket_notification(user_id, notification):
    """Send notification via WebSocket"""
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{user_id}',
            {
                'type': 'notification_message',
                'message': {
                    'id': notification.id,
                    'message': notification.message,
                    'type': notification.notification_type,
                    'time': notification.time,
                    'icon': notification.icon
                }
            }
        )
    except Exception as e:
        print(f"WebSocket error: {e}")
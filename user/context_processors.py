from seller.models import Product, ProductImage
from .models import CustomerNotification

def header_products(request):
    try:
        products = []
        for product in Product.objects.all():
            # Get the first image for this product
            first_image = ProductImage.objects.filter(product=product).first()
            image_url = first_image.image.url if first_image else '/static/images/default-product.png'
            
            products.append({
                'id': product.id,
                'name': product.name,
                'brand': product.brand,
                'price': product.price,
                'image_url': image_url
            })
        
        return {
            'header_products': products
        }
    except:
        return {
            'header_products': []
        }
        
        


def customer_notifications(request):
    if request.user.is_authenticated and request.user.role == 'customer':
        try:
            notifications = CustomerNotification.objects.filter(
                customer=request.user,
                is_read=False
            ).order_by('-created_at')[:10]
            
            print(f"🔔 [CUSTOMER CONTEXT] Found {notifications.count()} notifications for customer {request.user.username}")
            
            return {
                'customer_notifications': [
                    {
                        'icon': n.icon,
                        'message': n.message,
                        'time': n.time,
                        'type': n.notification_type,
                        'id': n.id
                    } for n in notifications
                ],
                'customer_unread_count': notifications.count()
            }
        except Exception as e:
            print(f"❌ [CUSTOMER CONTEXT] Error getting notifications: {e}")
            return {'customer_notifications': [], 'customer_unread_count': 0}
    return {'customer_notifications': [], 'customer_unread_count': 0}
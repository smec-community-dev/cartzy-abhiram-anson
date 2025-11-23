from django.urls import re_path
from user import consumers as user_consumers
from seller import consumers as seller_consumers

websocket_urlpatterns = [
    # User notifications
    re_path(r'ws/user/notifications/(?P<user_id>\w+)/$', user_consumers.UserNotificationConsumer.as_asgi()),
    # Seller notifications  
    re_path(r'ws/seller/notifications/(?P<user_id>\w+)/$', seller_consumers.NotificationConsumer.as_asgi()),
]
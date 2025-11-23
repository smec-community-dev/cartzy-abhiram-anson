from django.urls import re_path
from user import consumers

websocket_urlpatterns = [
    re_path(r'ws/user/notifications/(?P<user_id>\w+)/$', consumers.UserNotificationConsumer.as_asgi()),
]
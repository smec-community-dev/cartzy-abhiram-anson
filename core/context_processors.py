from .models import Notification  # Import from core

def notifications(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:10]
        
        return {
            'notifications': [
                {
                    'icon': n.icon,
                    'message': n.message,
                    'time': n.time,
                    'type': n.notification_type
                } for n in notifications
            ],
            'unread_count': notifications.count()
        }
    return {'notifications': [], 'unread_count': 0}
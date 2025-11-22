from seller.models import Notification

def notifications(request):
    if request.user.is_authenticated:
        try:
            notifications = Notification.objects.filter(
                seller=request.user,
                is_read=False
            ).order_by('-created_at')[:10]
            
            print(f"🔔 [CONTEXT] Found {notifications.count()} notifications for user {request.user.username}")
            
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
        except Exception as e:
            print(f"❌ [CONTEXT] Error getting notifications: {e}")
            return {'notifications': [], 'unread_count': 0}
    return {'notifications': [], 'unread_count': 0}
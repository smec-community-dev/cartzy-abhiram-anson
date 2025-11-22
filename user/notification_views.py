from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import CustomerNotification

@login_required
def customer_all_notifications(request):
    """Page showing ALL customer notifications with pagination"""
    if request.user.role != 'customer':
        return redirect('/')
    
    all_notifications = CustomerNotification.objects.filter(
        customer=request.user
    ).order_by('-created_at')
    
    # Handle clear actions
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'clear_all':
            # Clear all notifications
            all_notifications.delete()
            messages.success(request, 'All notifications cleared successfully.')
            return redirect('customer_all_notifications')
        elif action == 'clear_read':
            # Clear only read notifications
            read_notifications = all_notifications.filter(is_read=True)
            count = read_notifications.count()
            read_notifications.delete()
            messages.success(request, f'{count} read notifications cleared.')
            return redirect('customer_all_notifications')
    
    # Paginate - show 20 per page
    from django.core.paginator import Paginator
    paginator = Paginator(all_notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Counts for the template
    total_count = all_notifications.count()
    unread_count = all_notifications.filter(is_read=False).count()
    read_count = total_count - unread_count
    
    context = {
        'page_obj': page_obj,
        'notifications': page_obj.object_list,
        'total_count': total_count,
        'unread_count': unread_count,
        'read_count': read_count,
    }
    return render(request, 'user/customer_all_notifications.html', context)

@login_required
@require_http_methods(["DELETE"])
def clear_customer_notification(request, notification_id):
    """Clear a single customer notification (AJAX)"""
    if request.user.role != 'customer':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        notification = CustomerNotification.objects.get(
            id=notification_id, 
            customer=request.user
        )
        notification.delete()
        return JsonResponse({'success': True, 'message': 'Notification cleared'})
    except CustomerNotification.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Notification not found'}, status=404)

@login_required
def mark_customer_notification_read(request, notification_id):
    """Mark a customer notification as read (AJAX)"""
    if request.user.role != 'customer':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        notification = CustomerNotification.objects.get(
            id=notification_id, 
            customer=request.user
        )
        notification.is_read = True
        notification.save()
        
        # Get updated counts
        total_count = CustomerNotification.objects.filter(customer=request.user).count()
        unread_count = CustomerNotification.objects.filter(customer=request.user, is_read=False).count()
        read_count = total_count - unread_count
        
        return JsonResponse({
            'success': True, 
            'message': 'Notification marked as read',
            'counts': {
                'total': total_count,
                'unread': unread_count,
                'read': read_count
            }
        })
    except CustomerNotification.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Notification not found'}, status=404)
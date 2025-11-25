from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator
from datetime import timedelta
import json

from core.models import User, Category
from user.models import Order, Review, CustomerProfile
from seller.models import SellerProfile, Product, Notification

def admin_required(function=None):
    """
    Decorator for views that checks that the user is an admin (superuser or staff).
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and (u.is_superuser or u.is_staff),
        login_url='/login/'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

# ==================== ADMIN DASHBOARD ====================

@admin_required
def admin_dashboard(request):
    """
    Admin Dashboard View
    """
    # Calculate date ranges
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)
    
    # Today's Revenue Calculations
    today_revenue = Order.objects.filter(
        status='Delivered',
        created_at__date=today
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    yesterday_revenue = Order.objects.filter(
        status='Delivered',
        created_at__date=yesterday
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    revenue_change = 0
    if yesterday_revenue > 0:
        revenue_change = ((today_revenue - yesterday_revenue) / yesterday_revenue) * 100
    
    # Order Statistics
    total_orders_today = Order.objects.filter(created_at__date=today).count()
    total_orders_yesterday = Order.objects.filter(created_at__date=yesterday).count()
    
    orders_change = 0
    if total_orders_yesterday > 0:
        orders_change = ((total_orders_today - total_orders_yesterday) / total_orders_yesterday) * 100
    
    # User Statistics
    total_users = User.objects.count()
    
    # Active Products
    active_products = Product.objects.filter(is_active=True).count()
    
    # Platform Rating
    platform_rating_agg = Review.objects.aggregate(
        avg_rating=Avg('rating')
    )
    platform_rating = platform_rating_agg['avg_rating'] or 0
    total_reviews = Review.objects.count()
    
    # Pending Approvals
    pending_sellers_count = SellerProfile.objects.filter(is_verified=False).count()
    pending_products_count = Product.objects.filter(is_active=False).count()
    pending_orders_count = Order.objects.filter(status='Pending').count()
    low_stock_count = Product.objects.filter(stock__lt=10, stock__gt=0).count()
    
    # Recent Data
    recent_sellers = SellerProfile.objects.select_related('user').order_by('-id')[:5]
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:5]
    
    # Top Products (by order count)
    top_products = Product.objects.annotate(
        order_count=Count('orderitem')
    ).order_by('-order_count')[:4]
    
    # Best Sellers (by product count)
    best_sellers = SellerProfile.objects.annotate(
        product_count=Count('products')
    ).order_by('-product_count')[:4]
    
    # Recent Activity (using notifications)
    recent_activity = Notification.objects.all().order_by('-created_at')[:5]
    
    # Chart Data
    chart_data = get_platform_chart_data(7)
    
    # Notifications
    notifications = Notification.objects.filter(is_read=False).order_by('-created_at')[:5]
    unread_count = Notification.objects.filter(is_read=False).count()
    
    context = {
        # Stats for the template
        'today_revenue': today_revenue,
        'revenue_change': revenue_change,
        'total_orders_today': total_orders_today,
        'orders_change': orders_change,
        'total_users': total_users,
        'active_products': active_products,
        'platform_rating': platform_rating,
        'total_reviews': total_reviews,
        
        # Pending counts for quick actions
        'pending_sellers_count': pending_sellers_count,
        'pending_products_count': pending_products_count,
        'pending_orders_count': pending_orders_count,
        'low_stock_count': low_stock_count,
        
        # Recent data
        'recent_sellers': recent_sellers,
        'recent_users': recent_users,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'best_sellers': best_sellers,
        'recent_activity': recent_activity,
        
        # Chart data
        'chart_data': json.dumps(chart_data),
        
        # Notifications
        'notifications': notifications,
        'unread_count': unread_count,
    }
    
    return render(request, 'core/admin_dashboard.html', context)

def get_platform_chart_data(days=7):
    """
    Generate chart data for platform performance
    """
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    chart_data = []
    
    # Generate data for each day
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # Revenue for the day
        daily_revenue = Order.objects.filter(
            status='Delivered',
            created_at__date=current_date
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Orders for the day
        daily_orders = Order.objects.filter(
            created_at__date=current_date
        ).count()
        
        chart_data.append({
            'date': current_date.strftime('%b %d'),
            'revenue': float(daily_revenue),
            'orders': daily_orders,
        })
    
    return chart_data

# ==================== ADMIN MANAGEMENT PAGES ====================

@admin_required
def admin_users(request):
    """User Management Page"""
    users = User.objects.all().order_by('-date_joined')
    
    # Filtering
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    if role_filter:
        users = users.filter(role=role_filter)
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'core/admin_users.html', context)

@admin_required
def admin_user_detail(request, user_id):
    """User Detail Page"""
    user = get_object_or_404(User, id=user_id)
    
    # Get user's orders, reviews, etc.
    orders = Order.objects.filter(customer=user).order_by('-created_at')
    reviews = Review.objects.filter(customer=user).order_by('-created_at')
    
    if request.method == 'POST':
        # Handle user updates
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.is_active = request.POST.get('is_active') == 'on'
        user.save()
        
        messages.success(request, f'User {user.username} updated successfully!')
        return redirect('core:admin_user_detail', user_id=user.id)
    
    context = {
        'user_obj': user,
        'orders': orders,
        'reviews': reviews,
    }
    return render(request, 'core/admin_user_detail.html', context)

@admin_required
def admin_sellers(request):
    """Seller Management Page"""
    sellers = SellerProfile.objects.select_related('user').all().order_by('-id')
    
    # Filtering
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    if status_filter == 'verified':
        sellers = sellers.filter(is_verified=True)
    elif status_filter == 'pending':
        sellers = sellers.filter(is_verified=False)
    if search_query:
        sellers = sellers.filter(
            Q(shop_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(sellers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'sellers': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'core/admin_sellers.html', context)

@admin_required
def admin_seller_detail(request, seller_id):
    """Seller Detail Page"""
    seller = get_object_or_404(SellerProfile, id=seller_id)
    products = Product.objects.filter(seller=seller).order_by('-created_at')
    
    # Get orders for this seller
    orders = Order.objects.filter(items__product__seller=seller).distinct().order_by('-created_at')
    
    if request.method == 'POST':
        # Handle seller updates
        seller.shop_name = request.POST.get('shop_name', seller.shop_name)
        seller.is_verified = request.POST.get('is_verified') == 'on'
        seller.save()
        
        messages.success(request, f'Seller {seller.shop_name} updated successfully!')
        return redirect('core:admin_seller_detail', seller_id=seller.id)
    
    context = {
        'seller': seller,
        'products': products,
        'orders': orders,
    }
    return render(request, 'core/admin_seller_detail.html', context)

@admin_required
def admin_products(request):
    """Product Management Page"""
    products = Product.objects.select_related('seller', 'category').all().order_by('-created_at')
    
    # Filtering
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    
    if status_filter == 'active':
        products = products.filter(is_active=True)
    elif status_filter == 'inactive':
        products = products.filter(is_active=False)
    elif status_filter == 'low_stock':
        products = products.filter(stock__lt=10, stock__gt=0)
    
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(seller__shop_name__icontains=search_query)
        )
    
    categories = Category.objects.all()
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'search_query': search_query,
    }
    return render(request, 'core/admin_products.html', context)

@admin_required
def admin_product_detail(request, product_id):
    """Product Detail Page"""
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product).order_by('-created_at')
    
    if request.method == 'POST':
        # Handle product updates
        product.name = request.POST.get('name', product.name)
        product.description = request.POST.get('description', product.description)
        product.price = request.POST.get('price', product.price)
        product.stock = request.POST.get('stock', product.stock)
        product.is_active = request.POST.get('is_active') == 'on'
        product.is_featured = request.POST.get('is_featured') == 'on'
        product.save()
        
        messages.success(request, f'Product {product.name} updated successfully!')
        return redirect('core:admin_product_detail', product_id=product.id)
    
    context = {
        'product': product,
        'reviews': reviews,
    }
    return render(request, 'core/admin_product_detail.html', context)

@admin_required
def admin_orders(request):
    """Order Management Page"""
    orders = Order.objects.select_related('customer', 'address').all().order_by('-created_at')
    
    # Filtering
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(customer__username__icontains=search_query) |
            Q(customer__email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'core/admin_orders.html', context)

@admin_required
def admin_order_detail(request, order_id):
    """Order Detail Page"""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all()
    
    if request.method == 'POST':
        # Handle order updates
        order.status = request.POST.get('status', order.status)
        order.save()
        
        messages.success(request, f'Order #{order.order_number} updated successfully!')
        return redirect('core:admin_order_detail', order_id=order.id)
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'core/admin_order_detail.html', context)

@admin_required
def admin_categories(request):
    """Category Management Page"""
    categories = Category.objects.all().order_by('name')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if name:
            Category.objects.create(
                name=name,
                description=description
            )
            messages.success(request, 'Category created successfully!')
            return redirect('core:admin_categories')
    
    context = {
        'categories': categories,
    }
    return render(request, 'core/admin_categories.html', context)

@admin_required
def admin_category_detail(request, category_id):
    """Category Detail Page"""
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        category.is_active = request.POST.get('is_active') == 'on'
        category.save()
        
        messages.success(request, 'Category updated successfully!')
        return redirect('core:admin_categories')
    
    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'core/admin_category_detail.html', context)

@admin_required
def admin_reviews(request):
    """Review Management Page"""
    reviews = Review.objects.select_related('customer', 'product').all().order_by('-created_at')
    
    # Filtering
    rating_filter = request.GET.get('rating', '')
    search_query = request.GET.get('search', '')
    
    if rating_filter:
        reviews = reviews.filter(rating=rating_filter)
    
    if search_query:
        reviews = reviews.filter(
            Q(product__name__icontains=search_query) |
            Q(customer__username__icontains=search_query) |
            Q(review_text__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'reviews': page_obj,
        'rating_filter': rating_filter,
        'search_query': search_query,
    }
    return render(request, 'core/admin_reviews.html', context)

@admin_required
def admin_analytics(request):
    """Advanced Analytics Page"""
    # Time period for analytics
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Revenue analytics
    revenue_data = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).extra(
        {'date': "DATE(created_at)"}
    ).values('date').annotate(
        total_revenue=Sum('total_amount'),
        order_count=Count('id')
    ).order_by('date')
    
    # User analytics
    user_data = User.objects.filter(
        date_joined__date__gte=start_date,
        date_joined__date__lte=end_date
    ).extra(
        {'date': "DATE(date_joined)"}
    ).values('date').annotate(
        user_count=Count('id')
    ).order_by('date')
    
    # Top products
    top_products = Product.objects.annotate(
        total_sold=Count('orderitem'),
        total_revenue=Sum('orderitem__price')
    ).order_by('-total_sold')[:10]
    
    # Top sellers
    top_sellers = SellerProfile.objects.annotate(
        total_products=Count('products'),
        total_orders=Count('products__orderitem__order', distinct=True),
        total_revenue=Sum('products__orderitem__price')
    ).order_by('-total_revenue')[:10]
    
    # Category performance
    category_performance = Category.objects.annotate(
        product_count=Count('products'),
        active_products=Count('products', filter=Q(products__is_active=True))
    ).values('name', 'product_count', 'active_products')
    
    context = {
        'revenue_data': list(revenue_data),
        'user_data': list(user_data),
        'top_products': top_products,
        'top_sellers': top_sellers,
        'category_performance': list(category_performance),
        'days': days,
    }
    return render(request, 'core/admin_analytics.html', context)

@admin_required
def admin_settings(request):
    """Admin Settings Page"""
    if request.method == 'POST':
        # Handle settings update
        # You can add settings logic here
        messages.success(request, 'Settings updated successfully!')
        return redirect('core:admin_settings')
    
    return render(request, 'core/admin_settings.html')

@admin_required
def admin_notifications(request):
    """View all notifications for admin"""
    notifications = Notification.objects.all().order_by('-created_at')
    
    # Mark all as read when viewing all notifications
    if request.method == 'POST':
        Notification.objects.filter(is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read!')
        return redirect('core:admin_notifications')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
    }
    return render(request, 'core/admin_notifications.html', context)

# ==================== API ENDPOINTS ====================

@admin_required
def verify_seller(request, seller_id):
    """API endpoint to verify a seller"""
    if request.method == 'POST':
        seller = get_object_or_404(SellerProfile, id=seller_id)
        seller.is_verified = True
        seller.save()
        
        # Create notification for seller
        Notification.objects.create(
            seller=seller.user,
            message=f"Your seller account for {seller.shop_name} has been verified!",
            notification_type='info'
        )
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@admin_required
def deactivate_user(request, user_id):
    """API endpoint to deactivate a user"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_active = False
        user.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@admin_required
def activate_user(request, user_id):
    """API endpoint to activate a user"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_active = True
        user.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# ==================== PUBLIC PAGES ====================

def home(request):
    """Home page"""
    # Get featured products
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    
    # Get categories
    categories = Category.objects.filter(is_active=True)[:6]
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, 'core/home.html', context)

def about(request):
    """About page"""
    return render(request, 'core/about.html')

def contact(request):
    """Contact page"""
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        # Here you would typically send an email or save to database
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return redirect('core:contact')
    
    return render(request, 'core/contact.html')

def privacy_policy(request):
    """Privacy policy page"""
    return render(request, 'core/privacy.html')

def terms_of_service(request):
    """Terms of service page"""
    return render(request, 'core/terms.html')
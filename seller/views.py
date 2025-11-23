from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, authenticate, login
from .models import Product, SellerProfile, Category, ProductImage
from django.contrib import messages
from django.db.models import Prefetch
from django.utils.text import slugify
from django.db.models import Count, Q
from django.db.models import Q, Sum, Count
from user.models import Order, OrderItem
from django.core.paginator import Paginator
from django.http import JsonResponse    
import random
import string
from django.utils import timezone
from django.core.paginator import Paginator
import json
from django.db.models import Q, Count, Case, When, IntegerField
from django.contrib import messages
from django.db.models import F
User = get_user_model()


def seller_register(request):
    if request.method == "POST":
        print("HI")
        firstname = request.POST["firstname"]
        lastname = request.POST["lastname"]
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]
        shop_name = request.POST["shop_name"]
        contact_number = request.POST["phone"]
        gst_number = request.POST["gst_number"]
        address = request.POST["address"]

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("/seller/register/")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("/seller/register/")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("/seller/register/")

        user = User.objects.create_user(
            first_name=firstname,
            last_name=lastname,
            username=username,
            email=email,
            password=password,
            role="seller"
        )

        SellerProfile.objects.create(
            user=user,
            shop_name=shop_name,
            gst_number=gst_number,
            address=address,
            contact_number=contact_number
        )

        messages.success(request, "Account created successfully!")
        return redirect("/seller/login/")

    return render(request, "seller/seller_register.html")


def seller_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username or password")
            return redirect("/seller/login")

        if user.role != "seller":
            messages.error(request, "This login is only for sellers")
            return redirect("/seller/login")

        try:
            seller = user.seller_profile
        except SellerProfile.DoesNotExist:
            messages.error(request, "Please complete your seller profile.")
            return redirect("/seller/register")

        login(request, user)
        return redirect("/seller/dashboard")

    return render(request, "seller/seller_login.html")
# views.py

from django.utils import timezone
from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Avg
import json

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Avg
import json
from seller.models import Notification
@login_required
def seller_dashboard(request):
    try:
        # Import Review model
        from user.models import Review
        from seller.models import Notification
        # Get the seller profile for the current user
        seller_profile = SellerProfile.objects.get(user=request.user)
        
        print(f"\n=== DEBUGGING SELLER DASHBOARD ===")
        print(f"Seller Profile: {seller_profile}")
        print(f"Seller ID: {seller_profile.id}")
        
        # ========== ADD NOTIFICATIONS WITH 10-LIMIT ==========
        notifications = Notification.objects.filter(
            seller=request.user
        ).order_by('-created_at')[:10]
        print(f"Notifications count: {notifications.count()}")
        
       
        unread_count = Notification.objects.filter(
            seller=request.user,
            is_read=False
        ).count()
        print(f"Unread notifications: {unread_count}")
        # =====================================================
        
        # Basic stats
        total_products = Product.objects.filter(seller=seller_profile).count()
        print(f"Total Products: {total_products}")
        
        in_stock_products = Product.objects.filter(seller=seller_profile, stock__gt=0).count()
        low_stock_products = Product.objects.filter(seller=seller_profile, stock__lt=10, stock__gt=0).count()
        categories_count = Product.objects.filter(seller=seller_profile).values('category').distinct().count()
        
        # Sales metrics
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)
        last_month = today - timedelta(days=30)
        
        # Get seller's products
        seller_products = Product.objects.filter(seller=seller_profile)
        seller_product_ids = list(seller_products.values_list('id', flat=True))
        print(f"Seller Product IDs: {seller_product_ids}")
        
        # Check all orders in the system
        all_orders = Order.objects.all()
        print(f"\nTotal Orders in System: {all_orders.count()}")
        
        # Check order statuses
        if all_orders.exists():
            print("\nOrder Statuses in Database:")
            statuses = Order.objects.values_list('status', flat=True).distinct()
            for status in statuses:
                count = Order.objects.filter(status=status).count()
                print(f"  - '{status}': {count} orders")
        
        # Check orders with seller's products
        orders_with_seller_products = Order.objects.filter(
            items__product__in=seller_products
        ).distinct()
        print(f"\nOrders containing seller's products: {orders_with_seller_products.count()}")
        
        # Try different status variations
        status_variations = [
            'completed', 'Completed', 'COMPLETED',
            'delivered', 'Delivered', 'DELIVERED',
            'pending', 'Pending', 'PENDING',
            'shipped', 'Shipped', 'SHIPPED',
            'processing', 'Processing', 'PROCESSING'
        ]
        
        print("\nChecking different status variations:")
        for status in status_variations:
            count = Order.objects.filter(
                items__product__in=seller_products,
                status=status
            ).distinct().count()
            if count > 0:
                print(f"  - Status '{status}': {count} orders")
        
        # Get ALL orders (regardless of status) for today
        print(f"\nOrders for today ({today}):")
        today_all_orders = Order.objects.filter(
            items__product__in=seller_products,
            created_at__date=today
        ).distinct()
        print(f"  Total orders today (any status): {today_all_orders.count()}")
        
        # Check order items
        if today_all_orders.exists():
            print("\n  Today's Orders Details:")
            for order in today_all_orders:
                print(f"    Order #{order.order_number or order.id}:")
                print(f"      Status: '{order.status}'")
                print(f"      Total Amount: {order.total_amount}")
                seller_items = order.items.filter(product__in=seller_products)
                print(f"      Seller's Items: {seller_items.count()}")
                for item in seller_items:
                    print(f"        - {item.product_name}: ₹{item.price} x {item.quantity}")
        
        # Calculate revenue with ALL statuses first (for debugging)
        today_orders_all_status = Order.objects.filter(
            items__product__in=seller_products,
            created_at__date=today
        ).distinct()
        
        today_revenue = 0
        for order in today_orders_all_status:
            for order_item in order.items.filter(product__in=seller_products):
                item_revenue = float(order_item.price) * order_item.quantity
                today_revenue += item_revenue
                print(f"    Adding revenue: ₹{item_revenue} (from order #{order.order_number or order.id})")
        
        print(f"\nTotal Today's Revenue (all statuses): ₹{today_revenue}")
        
        # Now try with specific statuses
        # Get unique statuses from actual orders
        actual_statuses = list(Order.objects.filter(
            items__product__in=seller_products
        ).values_list('status', flat=True).distinct())
        
        print(f"\nActual order statuses for seller's products: {actual_statuses}")
        
        # Yesterday's revenue
        yesterday_orders = Order.objects.filter(
            items__product__in=seller_products,
            created_at__date=yesterday
        ).distinct()
        
        yesterday_revenue = 0
        for order in yesterday_orders:
            for order_item in order.items.filter(product__in=seller_products):
                yesterday_revenue += float(order_item.price) * order_item.quantity
        
        # Calculate revenue change percentage
        revenue_change = 0
        if yesterday_revenue > 0:
            revenue_change = round(((today_revenue - yesterday_revenue) / yesterday_revenue) * 100, 1)
        elif today_revenue > 0:
            revenue_change = 100.0
        
        # Total orders
        total_orders = Order.objects.filter(
            items__product__in=seller_products
        ).distinct().count()
        
        last_week_orders = Order.objects.filter(
            items__product__in=seller_products,
            created_at__date__gte=last_week
        ).distinct().count()
        
        # Calculate orders change percentage
        orders_change = 0
        prev_week_orders = total_orders - last_week_orders
        if prev_week_orders > 0:
            orders_change = round((last_week_orders / prev_week_orders) * 100, 1)
        elif last_week_orders > 0:
            orders_change = 100.0
        
        # Average rating
        average_rating = Review.objects.filter(
            product__seller=seller_profile
        ).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        average_rating = round(average_rating, 1)
        
        # Top products with sales data
        top_products = []
        for product in seller_products[:20]:
            # Get all order items for this product (ANY status for now)
            order_items = OrderItem.objects.filter(product=product)
            
            total_sold = sum(item.quantity for item in order_items)
            total_revenue = sum(float(item.price) * item.quantity for item in order_items)
            
            # Get the first image or use None if no images
            product_image = None
            product_image = product.images.filter(is_main=True).first() or product.images.first()
    
            
            if total_sold > 0:
                top_products.append({
                    'id': product.id,
                    'name': product.name,
                    'image': product_image,
                    'total_sold': total_sold,
                    'total_revenue': total_revenue
                })
        
        # Sort by total sold and take top 5
        top_products = sorted(top_products, key=lambda x: x['total_sold'], reverse=True)[:5]
        
        # Recent reviews
        recent_reviews = Review.objects.filter(
            product__seller=seller_profile
        ).select_related('product').order_by('-created_at')[:5]
        
        # Recent orders
        recent_orders = Order.objects.filter(
            items__product__in=seller_products
        ).select_related('customer').distinct().order_by('-created_at')[:5]
        
        # Chart data - last 30 days - USE ALL ORDERS (remove status filter for debugging)
        print("\n=== GENERATING CHART DATA ===")
        chart_data = []
        for i in range(30):
            date = today - timedelta(days=29-i)
            
            # Get orders for this date (ANY status)
            daily_orders = Order.objects.filter(
                items__product__in=seller_products,
                created_at__date=date
            ).distinct()
            
            # Calculate daily revenue
            daily_revenue = 0
            for order in daily_orders:
                for order_item in order.items.filter(product__in=seller_products):
                    daily_revenue += float(order_item.price) * order_item.quantity
            
            daily_order_count = daily_orders.count()
            
            if daily_order_count > 0 or daily_revenue > 0:
                print(f"{date.strftime('%b %d')}: {daily_order_count} orders, ₹{daily_revenue}")
            
            chart_data.append({
                'date': date.strftime('%b %d'),
                'revenue': round(daily_revenue, 2),
                'orders': daily_order_count
            })
        
        print(f"\nChart Data Generated: {len(chart_data)} points")
        print("Chart Data:", chart_data)
        
        context = {
            # ========== ADD NOTIFICATIONS TO CONTEXT ==========
            'notifications': notifications,
            'unread_count': unread_count,  
            # ==================================================
            
            'total_products': total_products,
            'in_stock_products': in_stock_products,
            'low_stock_products': low_stock_products,
            'categories_count': categories_count,
            'today_revenue': today_revenue,
            'revenue_change': revenue_change,
            'total_orders': total_orders,
            'orders_change': orders_change,
            'average_rating': average_rating,
            'top_products': top_products,
            'recent_reviews': recent_reviews,
            'recent_orders': recent_orders,
            'chart_data': json.dumps(chart_data),
        }
        
    except SellerProfile.DoesNotExist:
        context = {
            'error': 'Seller profile not found. Please complete your seller profile setup.',
            'notifications': [],  
            'unread_count': 0,   
            'total_products': 0,
            'in_stock_products': 0,
            'low_stock_products': 0,
            'categories_count': 0,
            'today_revenue': 0,
            'revenue_change': 0,
            'total_orders': 0,
            'orders_change': 0,
            'average_rating': 0,
            'top_products': [],
            'recent_reviews': [],
            'recent_orders': [],
            'chart_data': json.dumps([]),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in seller_dashboard: {str(e)}")
        
        context = {
            'error': f'An error occurred: {str(e)}',
            'notifications': [],  
            'unread_count': 0,   
            'total_products': 0,
            'in_stock_products': 0,
            'low_stock_products': 0,
            'categories_count': 0,
            'today_revenue': 0,
            'revenue_change': 0,
            'total_orders': 0,
            'orders_change': 0,
            'average_rating': 0,
            'top_products': [],
            'recent_reviews': [],
            'recent_orders': [],
            'chart_data': json.dumps([]),
        }
    
    return render(request, 'seller/seller_dashboard.html', context)
@login_required
def add_product(request):
    seller = request.user.seller_profile

    if request.method == "POST":
        try:
            name = request.POST["name"]
            price = request.POST["price"]
            description = request.POST["description"]
            brand = request.POST.get("brand", "")  
            category_id = request.POST["category"]
            stock = request.POST["stock"]

            category = Category.objects.get(id=category_id)
            sku = generate_sku(category)

            base_slug = slugify(name)
            slug = base_slug
            counter = 1

            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            product = Product.objects.create(
                seller=seller,
                category=category,
                name=name,
                sku=sku,
                slug=slug,
                price=price,
                stock=stock,
                description=description,
                brand=brand
            )

            images = request.FILES.getlist("images[]")
            main_index = int(request.POST.get("main_image", 0))
            
            print(f"Received {len(images)} images")
            print(f"Main image index: {main_index}")

            # Validate main_index to prevent index errors
            if main_index >= len(images) or main_index < 0:
                main_index = 0
                print(f"Adjusted main image index to: {main_index}")

            # Create all images
            for i, img in enumerate(images):
                is_main = (i == main_index)
                print(f"Creating image {i}: {img.name}, is_main: {is_main}")
                ProductImage.objects.create(
                    product=product,
                    image=img,
                    is_main=is_main
                )
            
            # Double-check that we have a main image set
            if not product.images.filter(is_main=True).exists():
                print("No main image found, setting first image as main")
                first_image = product.images.first()
                if first_image:
                    first_image.is_main = True
                    first_image.save()

            messages.success(request, "Product added successfully!")
            return redirect("/seller/dashboard")
            
        except Exception as e:
            print(f"Error creating product: {e}")
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, "seller/add_product.html", {
                "category": Category.objects.all(),
                "error": f"An error occurred: {str(e)}"
            })

    return render(request, "seller/add_product.html", {
        "category": Category.objects.all(),
    })
def generate_sku(category):
    
    category_prefix = category.name[:3].upper()
    timestamp = timezone.now().strftime('%y%m%d%H%M%S') 
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{category_prefix}{timestamp}{random_chars}"

from django.shortcuts import get_object_or_404

@login_required
def update_product(request, product_id):
    seller = request.user.seller_profile
    product = get_object_or_404(Product, id=product_id, seller=seller)
    images = product.images.all()  
    categories = Category.objects.all()

    if request.method == "POST":
        # Get form data
        name = request.POST["name"]
        description = request.POST["description"]
        category_id = request.POST["category"]
        brand = request.POST.get("brand", "")
        price = request.POST["price"]
        stock = request.POST["stock"]
        
        # Handle is_active toggle
        is_active = 'is_active' in request.POST
        
        # Get image management data
        current_main_image = request.POST.get("current_main_image", "")
        images_to_remove = request.POST.get("images_to_remove", "")
        
        print(f"Form data - is_active: {is_active}, current_main_image: {current_main_image}, images_to_remove: {images_to_remove}")

        # Update product basic info
        category = Category.objects.get(id=category_id)
        product.name = name
        product.description = description
        product.category = category
        product.brand = brand
        product.price = price
        product.stock = stock
        product.is_active = is_active
        product.save()

        # Handle image removal
        if images_to_remove:
            remove_ids = [int(id) for id in images_to_remove.split(',') if id.strip()]
            ProductImage.objects.filter(id__in=remove_ids, product=product).delete()
            print(f"Removed images: {remove_ids}")

        # Handle main image update
        # First, clear all existing main images
        ProductImage.objects.filter(product=product, is_main=True).update(is_main=False)
        
        # Check if main image is a new image or existing image
        if current_main_image:
            if current_main_image.startswith('new_'):
                # New image will be set as main after upload
                pass
            elif current_main_image.isdigit():
                # Set existing image as main
                ProductImage.objects.filter(id=int(current_main_image), product=product).update(is_main=True)
                print(f"Set existing image as main: {current_main_image}")

        # Handle new image uploads
        new_images = request.FILES.getlist("images[]")
        if new_images:
            # Find which new image should be main
            main_image_index = -1
            if current_main_image and current_main_image.startswith('new_'):
                # Extract index from new image ID (e.g., "new_123456789_0" -> index 0)
                try:
                    main_image_index = int(current_main_image.split('_')[2])
                except (IndexError, ValueError):
                    main_image_index = 0
            
            for i, img in enumerate(new_images):
                is_main = (i == main_image_index)
                ProductImage.objects.create(
                    product=product,
                    image=img,
                    is_main=is_main
                )
                if is_main:
                    print(f"Set new image as main: index {i}")
            
            print(f"Added {len(new_images)} new images")

        return redirect("/seller/products")

    # For GET request, pass main image ID to template
    main_image = images.filter(is_main=True).first()
    main_image_id = main_image.id if main_image else ""
    
    return render(request, "seller/update_product.html", {
        "product": product,
        "images": images,
        "categories": categories,
        "main_image_id": main_image_id,
    })


@login_required
def delete_product(request, product_id):
    seller = request.user.seller_profile
    product = Product.objects.filter(id=product_id, seller=seller).first()
    
    if not product:
        messages.error(request, "Product not found or unauthorized.")
        return redirect("seller:seller_products")

    if request.method == 'POST':
        # Always use soft delete - just deactivate, don't change stock
        product.is_active = False
        product.save()
        
        messages.success(request, f'"{product.name}" has been deactivated and hidden from customers.')
        return redirect("seller:seller_products")
    
    # If it's a GET request (shouldn't happen with modal), redirect back
    messages.warning(request, "Invalid request method.")
    return redirect("seller:seller_products")

@login_required
def seller_products(request):
    seller = request.user.seller_profile
    
    # Get all products for the current seller with optimizations
    products = Product.objects.filter(seller=seller).select_related('category').prefetch_related('images')
    
    # Get filter parameters from request
    category_filter = request.GET.get('category', '')
    stock_status_filter = request.GET.get('stock_status', '')
    sort_by = request.GET.get('sort_by', 'name')
    
    product_status = request.GET.get('product_status', '')
    if product_status == 'active':
        products = products.filter(is_active=True)
    elif product_status == 'inactive':
        products = products.filter(is_active=False)
    
    # Apply category filter
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    # Apply stock status filter
    if stock_status_filter == 'in_stock':
        products = products.filter(stock__gt=10)
    elif stock_status_filter == 'low_stock':
        products = products.filter(stock__gt=0, stock__lte=10)
    elif stock_status_filter == 'out_of_stock':
        products = products.filter(stock=0)
    
    # Apply sorting
    if sort_by == 'price':
        products = products.order_by('price')
    elif sort_by == 'stock':
        products = products.order_by('stock')
    elif sort_by == 'date':
        products = products.order_by('-created_at')
    else:  # default sort by name
        products = products.order_by('name')
    
    # Get stats (using original unfiltered queryset for accurate counts)
    total_products = Product.objects.filter(seller=seller).count()
    in_stock_products = Product.objects.filter(seller=seller, stock__gt=10).count()
    low_stock_products = Product.objects.filter(seller=seller, stock__gt=0, stock__lte=10).count()
    out_of_stock_products = Product.objects.filter(seller=seller, stock=0).count()
    
    # Get all categories
    categories = Category.objects.all()
    
    # Pagination
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add main image to each product for template
    for p in page_obj:
        main_img = p.images.filter(is_main=True).first()
        p.main_image_obj = main_img if main_img else p.images.first()

    for p in page_obj:
        p.is_inactive = not p.is_active

    context = {
        'products': page_obj,
        'total_products': total_products,
        'in_stock_products': in_stock_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'categories': categories,
        'selected_category': category_filter,
        'selected_stock_status': stock_status_filter,
        'selected_sort': sort_by,
    }
    
    return render(request, 'seller/products.html', context)

@login_required
def product_detail(request, product_id):
    seller = request.user.seller_profile
    
    
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images'),
        id=product_id,
        seller=seller
    )

    related_products = Product.objects.filter(
        seller=seller,
        category=product.category
    ).exclude(id=product.id).prefetch_related('images')[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    
    return render(request, 'seller/product_detail.html', context)


@login_required
def seller_orders(request):
    seller = request.user.seller_profile
    print(f"Seller ID: {seller.id}, Seller: {seller}")
    # Get all orders that contain products from this seller
    orders = Order.objects.filter(
        items__product__seller=seller
    ).distinct().select_related('customer', 'address').prefetch_related(
        'items__product__images'
    ).order_by('-created_at')
    print(f"Total orders found: {orders.count()}")
    for order in orders:
        seller_items_count = order.items.filter(product__seller=seller).count()
        print(f"Order #{order.order_number}: {seller_items_count} items from this seller")
        if seller_items_count == 0:
            print(f"  WARNING: Order {order.order_number} has no items from this seller!")
    # Apply filters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(customer__first_name__icontains=search_query) |
            Q(customer__last_name__icontains=search_query) |
            Q(items__product_name__icontains=search_query)
        ).distinct()
    
    # Calculate statistics
    total_orders = orders.count()
    pending_orders = orders.filter(status='Pending').count()
    processing_orders = orders.filter(status='Processing').count()
    shipped_orders = orders.filter(status='Shipped').count()
    delivered_orders = orders.filter(status='Delivered').count()
    
    # Calculate total revenue from delivered orders
    revenue = OrderItem.objects.filter(
        product__seller=seller,
        order__status='Delivered'
    ).aggregate(total_revenue=Sum('price'))['total_revenue'] or 0
    
    # Calculate seller subtotal for each order and attach main images
    for order in orders:
        order.seller_subtotal = 0
        for item in order.items.all():
            if item.product and item.product.seller == seller:
                # Calculate seller's subtotal
                order.seller_subtotal += item.price * item.quantity
                
                # Attach main image to product
                main_img = item.product.images.filter(is_main=True).first()
                item.product.main_image_obj = main_img if main_img else item.product.images.first()
    
    # Pagination
    paginator = Paginator(orders, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'total_revenue': revenue,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'seller/orders.html', context)




@login_required
def seller_profile(request):
    seller = request.user.seller_profile
    
    if request.method == "POST":
    
        request.user.first_name = request.POST.get("first_name", "")
        request.user.last_name = request.POST.get("last_name", "")
        request.user.email = request.POST.get("email", "")
        request.user.save()
        
        
        seller.shop_name = request.POST.get("shop_name", "")
        seller.contact_number = request.POST.get("contact_number", "")
        seller.gst_number = request.POST.get("gst_number", "")
        seller.address = request.POST.get("address", "")
        seller.save()
        
        messages.success(request, "Profile updated successfully!")
        return redirect('seller:seller_profile')
    
    context = {
        'seller': seller,
    }
    return render(request, 'seller/profile.html', context)
from django.db.models import Avg, Count, Q
from user.models import Review, Order, OrderItem  

# In seller/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from user.models import Review  # Import from user app
from .models import SellerReply, Product, SellerProfile

def seller_reviews(request):
    seller = request.user.seller_profile
    search_query = request.GET.get('search', '')
    rating_filter = request.GET.get('rating', '')
    selected_product_id = request.GET.get('product', '')

    # Get seller's products with reviews
    products_with_reviews = Product.objects.filter(
        seller=seller,
        reviews__isnull=False
    ).distinct()
    
    # Apply search filter
    if search_query:
        products_with_reviews = products_with_reviews.filter(
            Q(name__icontains=search_query) | 
            Q(sku__icontains=search_query)
        )
    
    # Apply rating filter
    if rating_filter:
        min_rating = int(rating_filter)
        products_with_reviews = products_with_reviews.filter(
            reviews__rating__gte=min_rating
        ).distinct()
    
    # Calculate stats
    total_reviews = Review.objects.filter(product__seller=seller).count()
    average_rating = Review.objects.filter(
        product__seller=seller
    ).aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Calculate response rate
    replied_reviews = Review.objects.filter(
        product__seller=seller,
        seller_replies__isnull=False
    ).count()
    response_rate = round((replied_reviews / total_reviews * 100) if total_reviews > 0 else 0, 1)
    
    # Get selected product and its reviews
    selected_product = None
    product_reviews = []
    
    if selected_product_id:
        try:
            selected_product = Product.objects.get(
                id=selected_product_id, 
                seller=seller
            )
            product_reviews = Review.objects.filter(
                product=selected_product
            ).select_related('customer').prefetch_related('seller_replies').order_by('-created_at')
            
        except Product.DoesNotExist:
            selected_product = None
    
    # Pagination for products
    paginator = Paginator(products_with_reviews, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    # Add review counts, average ratings, and main image to products
    for product in products:
        product.review_count = product.reviews.count()
        product_avg = product.reviews.aggregate(Avg('rating'))['rating__avg']
        product.avg_rating = round(product_avg, 1) if product_avg else 0
        
        # Fix: Get main image properly and use consistent naming
        product.main_image_obj = product.images.filter(is_main=True).first() or product.images.first()
    
    context = {
        'products': products,
        'selected_product': selected_product,
        'product_reviews': product_reviews,
        'total_reviews': total_reviews,
        'average_rating': round(average_rating, 1),
        'response_rate': response_rate,
        'search_query': search_query,
        'rating_filter': rating_filter,
        'selected_product_id': selected_product_id,
    }
    
    return render(request, 'seller/reviews.html', context)
@require_POST
@csrf_exempt
@login_required
def add_seller_reply(request, review_id):
    try:
        from user.models import Review
        from .models import SellerReply
        
        review = Review.objects.get(id=review_id)
        seller = request.user.seller_profile
        
        # Check if the review belongs to seller's product
        if review.product.seller != seller:
            return JsonResponse({'success': False, 'error': 'Unauthorized'})
        
        reply_text = request.POST.get('reply', '').strip()
        
        if not reply_text:
            return JsonResponse({'success': False, 'error': 'Reply text is required'})
        
        # Create new reply (allows multiple replies)
        seller_reply = SellerReply.objects.create(
            review=review,
            reply_text=reply_text,
            seller=seller
        )
        
        # Create notification for the user
        try:
            from user.utils import create_seller_reply_notification
            create_seller_reply_notification(seller_reply)
            print(f"Notification created for seller reply to review #{review_id}")
        except Exception as e:
            print(f"Error creating notification for seller reply: {e}")
            # Don't fail the reply if notification fails
        
        return JsonResponse({
            'success': True,
            'reply_text': seller_reply.reply_text,
            'replied_at': seller_reply.replied_at.strftime('%b %d, %Y'),
            'seller_name': seller.user.get_full_name(),
            'reply_id': seller_reply.id
        })
        
    except Review.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Review not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch

@login_required
def order_details(request, order_id):
    seller = request.user.seller_profile

    try:
        # Check if seller has items in this order
        order_exists = Order.objects.filter(
            id=order_id,
            items__product__seller=seller
        ).exists()

        if not order_exists:
            return JsonResponse({
                'success': False,
                'error': 'Order not found or not accessible'
            }, status=404)

        # Fetch order + prefetch images
        order = (
            Order.objects
            .filter(id=order_id, items__product__seller=seller)
            .select_related('customer', 'address')
            .prefetch_related(
                Prefetch(
                    'items',
                    queryset=(
                        OrderItem.objects
                        .filter(product__seller=seller)
                        .select_related('product')
                        .prefetch_related('product__images')
                    )
                )
            )
        ).first()

        seller_items = order.items.filter(product__seller=seller)

        # Subtotal
        seller_subtotal = sum((item.price or 0) * item.quantity for item in seller_items)

        # Build JSON items (RELIABLE VERSION)
        items_data = []
        for item in seller_items:
            product = item.product

            # Fetch main image directly from the DB
            main_img = None
            if product:
                main_img = product.images.filter(is_main=True).first()
                if not main_img:
                    main_img = product.images.first()

            image_url = request.build_absolute_uri(main_img.image.url) if main_img else None

            items_data.append({
                "product_name": item.product_name,
                "product_sku": item.product_sku,
                "quantity": item.quantity,
                "price": float(item.price or 0),
                "image_url": image_url
            })

        # Address JSON
        address = order.address
        address_data = (
            {
                "full_name": address.full_name,
                "phone": address.phone,
                "street": address.street,
                "city": address.city,
                "state": address.state,
                "postal_code": address.postal_code,
                "country": address.country,
            }
            if address else None
        )

        # Final response
        response_data = {
            "order_number": order.order_number,
            "created_at": order.created_at.isoformat(),
            "status": order.status,
            "customer_name": order.customer.get_full_name(),
            "customer_email": order.customer.email,
            "total_amount": float(order.total_amount),
            "seller_subtotal": float(seller_subtotal),
            "shipping_address": address_data,
            "items": items_data,
        }

        return JsonResponse({"success": True, "order": response_data})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "error": str(e)}, status=500)

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@login_required
def all_notifications(request):
    """Page showing ALL notifications with pagination"""
    from django.core.paginator import Paginator
    
    all_notifications = Notification.objects.filter(
        seller=request.user
    ).order_by('-created_at')
    
    # Handle clear actions
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'clear_all':
            # Clear all notifications
            all_notifications.delete()
            messages.success(request, 'All notifications cleared successfully.')
            return redirect('seller:all_notifications')
        elif action == 'clear_read':
            # Clear only read notifications
            read_notifications = all_notifications.filter(is_read=True)
            count = read_notifications.count()
            read_notifications.delete()
            messages.success(request, f'{count} read notifications cleared.')
            return redirect('seller:all_notifications')
    
    # Paginate - show 20 per page
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
    return render(request, 'seller/all_notifications.html', context)

@login_required
@require_http_methods(["DELETE"])
def clear_notification(request, notification_id):
    """Clear a single notification (AJAX)"""
    try:
        notification = Notification.objects.get(
            id=notification_id, 
            seller=request.user
        )
        notification.delete()
        return JsonResponse({'success': True, 'message': 'Notification cleared'})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Notification not found'}, status=404)

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read (AJAX)"""
    try:
        notification = Notification.objects.get(
            id=notification_id, 
            seller=request.user
        )
        notification.is_read = True
        notification.save()
        
        # Get updated counts
        total_count = Notification.objects.filter(seller=request.user).count()
        unread_count = Notification.objects.filter(seller=request.user, is_read=False).count()
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
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Notification not found'}, status=404)
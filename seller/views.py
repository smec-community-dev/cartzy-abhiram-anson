from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, authenticate, login
from .models import Product, SellerProfile, Category, ProductImage
from django.contrib import messages
from django.utils.text import slugify
from django.db.models import Count, Q
from django.db.models import Q, Sum, Count
from user.models import Order, OrderItem
from django.core.paginator import Paginator

import random
import string
from django.utils import timezone
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


@login_required
def seller_dashboard(request):
    seller = request.user.seller_profile
    products = seller.products.all().prefetch_related('images')
    
    # Calculate statistics for the dashboard
    total_products = products.count()
    in_stock_products = products.filter(stock__gt=0).count()
    low_stock_products = products.filter(stock__lt=10, stock__gt=0).count()
    
    # Get distinct categories count from seller's products
    categories_count = products.values('category').distinct().count()
    
    # Attach main_image to each product for template use
    for product in products:
        main_img = product.images.filter(is_main=True).first()
        product.main_image_obj = main_img if main_img else product.images.first()
        print(f"Product: {product.name}, Main Image: {main_img}, All images count: {product.images.count()}")
    
    context = {
        "products": products,
        "total_products": total_products,
        "in_stock_products": in_stock_products,
        "low_stock_products": low_stock_products,
        "categories_count": categories_count,
    }
    
    return render(request, "seller/seller_dashboard.html", context)
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
        name = request.POST["name"]
        description = request.POST["description"]
        category_id = request.POST["category"]
        brand = request.POST.get("brand", "")
        price = request.POST["price"]
        stock = request.POST["stock"]

        category = Category.objects.get(id=category_id)

        product.name = name
        product.description = description
        product.category = category
        product.brand = brand
        product.price = price
        product.stock = stock
        product.save()

        new_images = request.FILES.getlist("images[]")
        main_index = int(request.POST.get("main_image", 0))

        for i, img in enumerate(new_images):
            ProductImage.objects.create(
                product=product,
                image=img,
                is_main=(i == main_index)
            )

        return redirect("/seller/dashboard")

    return render(request, "seller/update_product.html", {
        "product": product,
        "images": images,
        "categories": categories,
    })


@login_required
def delete_product(request, product_id):
    seller = request.user.seller_profile

    product = Product.objects.filter(id=product_id, seller=seller).first()
    if not product:
        messages.error(request, "Product not found or unauthorized.")
        return redirect("/seller/dashboard")

    product.delete()
    messages.success(request, "Product deleted successfully!")

    return redirect("/seller/dashboard")


def main_image(self):
    return self.images.filter(is_main=True).first()

from django.core.paginator import Paginator
from django.db.models import Q, Count, Case, When, IntegerField
from django.contrib import messages

@login_required
def seller_products(request):
    seller = request.user.seller_profile
    
    products = Product.objects.filter(seller=seller).select_related('category').prefetch_related('images')
    
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', 'name')
    
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    if status_filter:
        if status_filter == 'in_stock':
            products = products.filter(stock__gt=10)
        elif status_filter == 'low_stock':
            products = products.filter(stock__gt=0, stock__lte=10)
        elif status_filter == 'out_of_stock':
            products = products.filter(stock=0)
    
    if sort_by == 'price':
        products = products.order_by('price')
    elif sort_by == 'stock':
        products = products.order_by('stock')
    elif sort_by == 'date':
        products = products.order_by('-created_at') 
    else:  
        products = products.order_by('name')
    
    total_products = products.count()
    in_stock_products = products.filter(stock__gt=10).count()
    low_stock_products = products.filter(stock__gt=0, stock__lte=10).count()
    out_of_stock_products = products.filter(stock=0).count()
    
    categories = Category.objects.all()
    
    paginator = Paginator(products, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # ✅ FIX — attach main image to each PRODUCT IN THE PAGE
    for p in page_obj:
        main_img = p.images.filter(is_main=True).first()
        p.main_image_obj = main_img if main_img else p.images.first()

    context = {
        'products': page_obj,
        'total_products': total_products,
        'in_stock_products': in_stock_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'categories': categories,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'sort_by': sort_by,
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
    
    # Get all orders that contain products from this seller
    orders = Order.objects.filter(
        items__product__seller=seller
    ).distinct().select_related('customer', 'address').prefetch_related('items').order_by('-created_at')
    
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
    
    # Pagination
    paginator = Paginator(orders, 15)  # 15 orders per page
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
        # Update user information
        request.user.first_name = request.POST.get("first_name", "")
        request.user.last_name = request.POST.get("last_name", "")
        request.user.email = request.POST.get("email", "")
        request.user.save()
        
        # Update seller profile information
        seller.shop_name = request.POST.get("shop_name", "")
        seller.contact_number = request.POST.get("contact_number", "")
        seller.gst_number = request.POST.get("gst_number", "")
        seller.address = request.POST.get("address", "")
        seller.save()
        
        messages.success(request, "Profile updated successfully!")
        return redirect('seller_profile')
    
    context = {
        'seller': seller,
    }
    return render(request, 'seller/profile.html', context)
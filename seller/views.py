from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, authenticate, login
from .models import Product, SellerProfile, Category, ProductImage
from django.contrib import messages

User = get_user_model()


def seller_register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        shop_name = request.POST["shop_name"]

    
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("seller_register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("seller_register")

        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role="seller"
        )

        
        SellerProfile.objects.create(
            user=user,
            shop_name=shop_name
        )

        return redirect("seller_login")

    return render(request, "seller/seller_register.html")



def seller_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username or password")
            return redirect("seller_login")

        
        if user.role != "seller":
            messages.error(request, "This login is only for sellers")
            return redirect("seller_login")

        
        try:
            seller = user.seller_profile
        except SellerProfile.DoesNotExist:
            messages.error(request, "Please complete your seller profile.")
            return redirect("seller_create_profile")

        login(request, user)
        return redirect("seller_dashboard")

    return render(request, "seller/seller_login.html")



@login_required
def seller_dashboard(request):
    seller = request.user.seller_profile
    products = seller.products.all()
    return render(request, "seller/dashboard.html", {"products": products})



@login_required
def add_product(request):
    seller = request.user.seller_profile

    if request.method == "POST":
        name = request.POST["name"]
        sku = request.POST["sku"]
        price = request.POST["price"]
        description = request.POST["description"]
        brand = request.POST.get("brand", "")  
        category_id = request.POST["category"]

        category = Category.objects.get(id=category_id)

        product = Product.objects.create(
            seller=seller,
            category=category,
            name=name,
            sku=sku,
            price=price,
            description=description,
            brand=brand
        )

    
        images = request.FILES.getlist("images")
        main_index = int(request.POST.get("main_image", 0))

        for i, img in enumerate(images):
            ProductImage.objects.create(
                product=product,
                image=img,
                is_main=(i == main_index)
            )

        return redirect("seller_dashboard")

    return render(request, "seller/add_product.html", {
        "category": Category.objects.all(),
    })

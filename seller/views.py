from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, authenticate, login
from .models import Product, SellerProfile, Category, ProductImage
from django.contrib import messages
from django.utils.text import slugify

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
    products = seller.products.all()
    return render(request, "seller/seller_dashboard.html", {"products": products})



@login_required
def add_product(request):
    seller = request.user.seller_profile

    if request.method == "POST":
        name = request.POST["name"]
        price = request.POST["price"]
        description = request.POST["description"]
        brand = request.POST.get("brand", "")  
        category_id = request.POST["category"]
        stock = request.POST["stock"]

        category = Category.objects.get(id=category_id)
        sku = generate_sku(category)

        # Generate unique slug
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

        for i, img in enumerate(images):
            ProductImage.objects.create(
                product=product,
                image=img,
                is_main=(i == main_index)
            )


        return redirect("/seller/dashboard")

    return render(request, "seller/add_product.html", {
        "category": Category.objects.all(),
    })


def generate_sku(category):
    category_prefix = category.name[:3].upper()

    count = Product.objects.filter(category=category).count() + 1

    number = str(count).zfill(4)

    return f"{category_prefix}-{number}"



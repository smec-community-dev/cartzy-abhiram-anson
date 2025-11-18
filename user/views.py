import datetime
import random
from django.shortcuts import render, redirect
from core.models import User
from .models import CustomerProfile, Cart, CartItem, Wishlist, Address, Order, OrderItem
from core.models import Category
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from seller.models import Product, ProductImage

def home_view(request):
    return render(request, 'user/index.html')

def about_view(request):
    return render(request, 'user/about.html')

def user_reg_view(request):
    if request.method=='POST':
        firstname=request.POST['firstname']
        lastname=request.POST['lastname']
        email=request.POST['email']
        username=request.POST['username']
        phone=request.POST['phone']
        password=request.POST['password']
        confirm_password=request.POST['confirm-password']            

        if confirm_password!=password:
            return HttpResponse('<script>alert("Passwords  doesnt match!!!");window.location.href="/UserReg/";</script>')
        
        if User.objects.filter(username = username).exists():
            return HttpResponse('<script>alert("User already exists!!!");window.location.href="/UserReg/";</script>')
        if User.objects.filter(email = email).exists():
            return HttpResponse('<script>alert("Email already exists!!!");window.location.href="/UserReg/";</script>')
        
        user=User.objects.create_user(first_name=firstname, last_name=lastname, email=email, username=username,password=password, role='customer')
        CustomerProfile.objects.create(user=user, phone=phone)
        return redirect('/login/')
        
    return render(request ,'user/user_reg.html')

def login_view(request):
    if request.method == 'POST':
        username=request.POST['username']
        password=request.POST['password']
        
        user=authenticate(username=username, password=password)
        if user is not None and user.role == 'customer':
            login(request, user)
            return redirect('/userhome/')
        else:
            return HttpResponse('<scripts>alert("Invalid!!!");</scripts>')
    return render(request, 'user/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')
    

def user_home_view(request):
    return render(request, 'user/user_home.html')

def user_category_view(request):
    Categories=Category.objects.all()    
    return render(request, 'user/user_view_category.html', {'categories':Categories})
        
        
def user_view_all_products(request):
    products=Product.objects.all()
    return render(request, 'user/user_view_products.html', {'products':products})

def user_view_products(request, id):
    products=Product.objects.filter(category_id = id)    
    return render(request, 'user/user_view_products.html',{'products':products})

def user_view_product_details(request, id):
    product_details=Product.objects.get(id=id)
    images=ProductImage.objects.filter(product_id=product_details.id)
    context={
        'product_details':product_details,
        'images':images
    }
    return render(request, 'user/user_view_single_products.html', context)

def user_add_to_cart(request, id):
    product_id=id
    user_id=request.user.id
    quantity=int(request.POST.get('quantity', 1))
    
    cart, creat=Cart.objects.get_or_create(customer_id=user_id)
    cartitem, created=CartItem.objects.get_or_create(cart=cart, product_id=product_id,  defaults={"quantity": quantity})
    if not created:
        cartitem.quantity+=quantity
        cartitem.save()
    return redirect (request.META.get('HTTP_REFERER', '/'))

def user_view_cart(request):
    user_id=request.user.id
    cart=Cart.objects.get(customer_id=user_id)
    cartitems=CartItem.objects.filter(cart_id=cart)
    subtotal=0
    for item in cartitems:
        subtotal+=item.subtotal()
    shipping = 50 
    grand_total = subtotal + shipping
    context={
        'cart':cart,
        'cartitems':cartitems,
        'subtotal':subtotal,
        'shipping':shipping,
        'grand_total':grand_total
    }
    return render(request, 'user/user_view_cart.html',{'context':context})

def user_remove_cart_item(request, id):
    cartitem=CartItem.objects.get(id=id)
    cartitem.delete()
    return redirect(request.META.get('HTTP_REFERER', '/'))  

def user_add_to_wishlist(request, id):
    user_id=request.user.id
    product_id=id
    if not Wishlist.objects.filter(product_id=product_id):
        Wishlist.objects.create(customer_id=user_id, product_id=product_id)
    return redirect (request.META.get('HTTP_REFERER', '/'))
    
def user_view_wishlist(request):
    user_id=request.user.id
    wish=Wishlist.objects.filter(customer_id=user_id)

    return render(request, 'user/user_view_wishlist.html', {'wish':wish})


def user_view_account(request):
    user_id=request.user.id
    user=User.objects.get(id=user_id)
    cust=CustomerProfile.objects.get(user_id=user_id)
    address=Address.objects.filter(customer_id=user_id).first()
    context={
        'username':user.username,
        'phone':cust.phone,
        'date_joined':user.date_joined,
        'first_name':user.first_name,
        'last_name':user.last_name,
        'email':user.email,
        'address_list': address
    }
    return render(request, 'user/user_view_account.html', {'context':context})

def user_update_account(request):
    user_id=request.user.id
    
    user=User.objects.get(id=user_id)
    cust=CustomerProfile.objects.get(user_id=user)
    address=Address.objects.filter(customer_id=user).first()
    
    context={
        'username':user.username,
        'phone':cust.phone,
        'date_joined':user.date_joined,
        'first_name':user.first_name,
        'last_name':user.last_name,
        'email':user.email,
        'address_list': address
    }
    if request.method=='POST':
        first_name=request.POST['firstname']
        email=request.POST['email']
        username=request.POST['username']
        street=request.POST['street']
        city=request.POST['city']
        last_name=request.POST['lastname']
        phno=request.POST['phone']
        postal=request.POST['postal']
        state=request.POST['state']
        country=request.POST['country']
        
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            return HttpResponse("<script>alert('username already exists!!!');</script>")
        
        user.first_name=first_name
        user.email=email
        user.username=username
        user.last_name=last_name
        user.save()
        
        cust.phone=phno
        cust.save()
        if address:
            address.street=street
            address.postal_code=postal
            address.city=city
            address.state=state
            address.country=country
            address.save()
        else:
            Address.objects.create(customer_id=user_id,full_name=user.first_name, phone=phno, street=street, city=city, state=state, postal_code=postal, country=country)
        
    return render(request, 'user/user_update_account.html', {'context':context})

def generate_order_number():
    today = datetime.datetime.now().strftime("%Y%m%d")  
    random_number = random.randint(1000, 9999)
    return f"ORD{today}{random_number}"

def user_proceed_to_checkout(request, id):
    customer=request.user.id
    cart=Cart.objects.get(id=id, customer_id=customer)
    address=Address.objects.get(customer_id=request.user)
    order_no=generate_order_number()
    tot_amount=cart.total_amount()

    
    cartitems=CartItem.objects.filter(cart_id=cart.id)
    order=Order.objects.create(customer_id = customer, 
                               address=address,
                               order_number=order_no, 
                               status ='Pending', 
                               total_amount=tot_amount)
    for item in cartitems:
        OrderItem.objects.create(order_id=order.id,
                                 product_id=item.product.id,
                                 product_name=item.product.name,
                                 product_sku=item.product.sku,
                                 quantity=item.quantity,
                                 price=item.product.price
                                 )
    cart.delete()
    return render(request, 'user/user_home.html')


def user_view_order(request):
    return render(request, 'user/user_view_orders.html')
    
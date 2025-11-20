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
    cartitem, created=CartItem.objects.get_or_create(cart_id=cart.id, product_id=product_id,  defaults={"quantity": quantity})
    if not created:
        cartitem.quantity+=quantity
        cartitem.save()
    return redirect (request.META.get('HTTP_REFERER', '/'))

def user_view_cart(request):
    user_id=request.user.id
    try:
        cart=Cart.objects.get(customer_id=user_id)
        cartitems=CartItem.objects.filter(cart_id=cart)
        subtotal=0
        for item in cartitems:
            subtotal+=item.subtotal()
        shipping = 50 
        grand_total = subtotal + shipping
        context={
            
            'cart_empty': False, 
            'cart':cart,
            'cartitems':cartitems,
            'subtotal':subtotal,
            'shipping':shipping,
            'grand_total':grand_total
        }
        
        
    except Cart.DoesNotExist:
        context={
            'cart_empty':True
        }
        print("HEllo")
    return render(request, 'user/user_view_cart.html',{'context':context})

def user_remove_cart_item(request, id):
    cartitem=CartItem.objects.get(id=id)
    cart=cartitem.cart
    cartitem.delete()
    if not CartItem.objects.filter(cart=cart).exists():
        cart.delete()
    return redirect('user_view_cart')
    

def user_add_to_wishlist(request, id):
    user_id=request.user.id
    product_id=id
    if not Wishlist.objects.filter(product_id=product_id, customer_id=user_id):
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
    print("HI")
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


# def user_proceed_to_checkout(request, id):
#     customer=request.user.id

#     cart=Cart.objects.get(id=id, customer_id=customer)
#     try:
#         address=Address.objects.get(customer_id=request.user)
#         order_no=generate_order_number()
#         tot_amount=cart.total_amount()        
#         cartitems=CartItem.objects.filter(cart_id=cart.id)
#         order=Order.objects.create(customer_id = customer, 
#                                 address=address,
#                                 order_number=order_no, 
#                                 status ='Pending', 
#                                 total_amount=tot_amount)
#         for item in cartitems:
#             OrderItem.objects.create(order_id=order.id,
#                                     product_id=item.product.id,
#                                     product_name=item.product.name,
#                                     product_sku=item.product.sku,
#                                     quantity=item.quantity,
#                                     price=item.product.price
#                                     )
#         cart.delete()
#     except Address.DoesNotExist:
#         return redirect("/userupdateaccount")
#     return render(request, 'user/user_home.html')


def user_view_order(request):
    user_id=request.user.id
    try:
        order=Order.objects.filter(customer_id=user_id)
        orderitems=OrderItem.objects.filter(order__in=order)
        context={
            'order':order,
            'orderitems':orderitems,
            'found':True
        }
    except Order.DoesNotExist:
        context={
            'found':False
        }
    return render(request, 'user/user_view_orders.html', context)


def user_add_addresses(request):
    user_id=request.user.id
    print("HI")
    address=Address.objects.filter(customer_id=user_id)
    if request.method=="POST":
        new_name=request.POST['new_name']
        new_phone=request.POST['new_phone']
        new_street=request.POST['new_street']
        new_city=request.POST['new_city']
        new_state=request.POST['new_state']
        new_postalcode=request.POST['new_postalcode']
        new_country=request.POST['new_country']
        is_default = 'is_default' in request.POST
        
        if is_default:
            Address.objects.filter(customer_id=user_id, is_default=True).update(is_default=False)
            
        addresses=Address.objects.create(customer_id=user_id, full_name=new_name, phone=new_phone, street=new_street, city=new_city, state=new_state,
                               postal_code=new_postalcode, country=new_country, is_default=is_default)
        return redirect('user_add_addresses')
    return render(request, 'user/user_add_addresses.html',{'addresses':address})




def user_confirm_order(request, id):
    user_id=request.user.id
    user=User.objects.get(id=user_id)
    customer_profile=CustomerProfile.objects.get(user_id=user_id)
    all_addresses = Address.objects.filter(customer_id=user_id)
    try:
        address=Address.objects.get(customer_id=user_id, is_default=True)   
    except Address.DoesNotExist:
        address=Address.objects.filter(customer_id=user_id).first()   
    cartitems=CartItem.objects.filter(cart_id=id)   
    sub_total=0
    for i in cartitems:
        sub_total+=i.subtotal()
    shipping=50
    grand_total= sub_total+shipping
    context={
        'cartitems':cartitems,
        'address':address,
        'all_addresses': all_addresses,
        'customer_profile':customer_profile,
        'user':user,
        'subtotal':sub_total,
        'shipping':shipping,
        'grand_total':grand_total,
        'cart': {'id': id}
    }

        
    return render(request, 'user/user_confirm_oder.html',context )

def user_choose_address(request):
    user_id=request.user.id
    address=Address.objects.filter(customer_id=request.user.id)
    if request.method == "POST":
        new_name = request.POST['new_name']
        new_phone = request.POST['new_phone']
        new_street = request.POST['new_street']
        new_city = request.POST['new_city']
        new_state = request.POST['new_state']
        new_postalcode = request.POST['new_postalcode']
        new_country = request.POST['new_country']

        is_default = 'is_default' in request.POST

        
        if is_default:
            Address.objects.filter(customer_id=user_id, is_default=True).update(is_default=False)

        Address.objects.create(
            customer_id=user_id,
            full_name=new_name,
            phone=new_phone,
            street=new_street,
            city=new_city,
            state=new_state,
            postal_code=new_postalcode,
            country=new_country,
            is_default=is_default
        )

        return redirect('user_choose_address')  
    return render(request, 'user/user_choose_address.html',{'addresses':address})

    
def user_update_order_address(request):
    if request.method=='POST':
        user_id=request.user.id
        cart_id=request.POST.get('cart_id')
        selected_address_id = request.POST.get('selected_address')
        try:
            Address.objects.filter(customer_id=user_id).update(is_default=False)
            
            
            selected_address = Address.objects.get(id=selected_address_id, customer_id=user_id)
            selected_address.is_default = True
            selected_address.save()
            
           
            return redirect('user_confirm_order', id=cart_id)
            
        except Exception as e:
            
            return redirect('user_confirm_order', id=cart_id)
    
    return redirect('user_confirm_order', id=cart_id)


def user_add_new_address(request):
    
    if request.method == 'POST':
       
        user_id = request.user.id
        cart_id = request.POST.get('cart_id')

        try:
            # Checkbox handling
            is_default = 'is_default' in request.POST

            # If new default, remove old defaults
            if is_default:
                Address.objects.filter(customer_id=user_id).update(is_default=False)

            # Create address
            Address.objects.create(
                customer_id=user_id,
                full_name=request.POST.get('new_name'),
                street=request.POST.get('new_street'),
                city=request.POST.get('new_city'),
                state=request.POST.get('new_state'),
                postal_code=request.POST.get('new_postalcode'),
                country=request.POST.get('new_country'),
                phone=request.POST.get('new_phone'),
                is_default=is_default
            )

            return redirect('user_confirm_order', id=cart_id)

        except Exception as e:
            print("Hkkki")
            print("ERROR:", e)
            return redirect('user_confirm_order', id=cart_id)

    return redirect('user_confirm_order', id=cart_id)

def create_order(request, id):
    user_id=request.user.id
    address_id=request.POST.get('selected_address')
    cart=Cart.objects.get(id=id, customer_id=user_id)
    cartitems=CartItem.objects.filter(cart_id=cart)
    order_no=generate_order_number()
    tot=0
    for i in cartitems:
       tot+=i.subtotal()
    order=Order.objects.create(order_number=order_no, status='Delivered', total_amount=tot, address_id=address_id, customer_id=user_id)
    for item in cartitems:        
        OrderItem.objects.create(product_name=item.product.name, product_sku=item.product.sku, quantity=item.quantity, price=item.product.price, order_id=order.id, product_id=item.product.id)
    cart.delete()
    
    return render(request, 'user/user_home.html')


def user_add_review(request, id):
    return render(request, 'user/user_add_review.html')
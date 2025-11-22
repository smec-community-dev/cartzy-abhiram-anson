import datetime
from django.contrib import messages
import random
from django.shortcuts import render, redirect
from core.models import User
from .models import CustomerProfile, Cart, CartItem, Wishlist, Address, Order, OrderItem, Review, ReviewImage
from core.models import Category
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from seller.models import Product, ProductImage, SellerProfile
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decorators.decorators import role_required
from django.shortcuts import get_object_or_404

from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages

class OAuthCancelView(View):
    def get(self, request):
        return render(request, 'oauth/cancel.html')

class OAuthErrorView(View):
    def get(self, request):
        error_message = request.GET.get('error', 'An unknown error occurred.')
        return render(request, 'oauth/error.html', {'error_message': error_message})

class AccountExistsView(View):
    def get(self, request):
        email = request.GET.get('email', '')
        return render(request, 'oauth/account_exists.html', {'email': email})

def set_google_customer(request):
    request.session["google_role"] = "customer"
    return redirect("/accounts/google/login/")


def set_google_seller(request):
    request.session["google_role"] = "seller"
    return redirect("/accounts/google/login/")

def role_redirect(request):
    user = request.user
    role = request.session.get("google_role", "customer")

    # Assign role only first time
    if not user.role:
        user.role = role
        user.save()

    # Create profile if not exists
    if role == "customer":
        CustomerProfile.objects.get_or_create(user=user)
        return redirect("user_home")

    elif role == "seller":
        SellerProfile.objects.get_or_create(user=user)
        return redirect("seller_home")

    return redirect("/")

def header_products(request):
    products = list(Product.objects.all().values('id', 'name', 'price', 'images'))
    return {
        'header_products': products
    }
    
    
    
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
    
@role_required("customer", login_url="/login/")
def user_home_view(request):
    return render(request, 'user/user_home.html')



def user_category_view(request):
    categories_list = Category.objects.all()
    paginator = Paginator(categories_list, 3)
    page = request.GET.get('page')
    
    try:
        categories = paginator.page(page)
    except PageNotAnInteger:
       
        categories = paginator.page(1)
    except EmptyPage:
        
        categories = paginator.page(paginator.num_pages)
    
    return render(request, 'user/user_view_category.html', {'categories': categories})
        
        


def user_view_all_products(request):
    # Get all products
    products = Product.objects.all()
    
    # Price filtering
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
    sort = request.GET.get('sort', '')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-id')  # Assuming newer products have higher IDs
    
    # Pagination
    paginator = Paginator(products, 2)
    page = request.GET.get('page')
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        'products': products,
    }
    return render(request, 'user/user_view_products.html', context)

def user_view_products(request, id):
    products_list = Product.objects.filter(category_id=id)
    
    # Also change this to 2 or 3
    paginator = Paginator(products_list, 2)  # ← Change to 2 or 3
    page = request.GET.get('page')
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    return render(request, 'user/user_view_products.html', {'products': products})

def user_view_product_details(request, id):
    product_details = Product.objects.get(id=id)
    images = ProductImage.objects.filter(product=product_details)
    
    # Check if the current user has already reviewed this product
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = Review.objects.filter(
            customer=request.user, 
            product=product_details
        ).exists()
    
    context = {
        'product_details': product_details,
        'images': images,
        'user_has_reviewed': user_has_reviewed,
    }
    
    return render(request, 'user/user_view_single_products.html', context)

@role_required("customer", login_url="/login/")
def user_add_to_cart(request, id):
    if not request.user.is_authenticated:
        messages.error(request, "Please login to add items to cart.")
        return redirect('user_login')
    
    try:
        product = Product.objects.get(id=id)
        user_id = request.user.id
        quantity = int(request.POST.get('quantity', 1))
        
        # Server-side validation
        if quantity < 1:
            messages.error(request, "Please select at least 1 item.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # Check if product has enough stock
        if quantity > product.stock:
            messages.error(request, f"Cannot add {quantity} items. Only {product.stock} available in stock.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # Check if adding this quantity would exceed stock (considering existing cart items)
        cart, created = Cart.objects.get_or_create(customer_id=user_id)
        try:
            cart_item = CartItem.objects.get(cart_id=cart.id, product_id=product.id)
            total_quantity_after_add = cart_item.quantity + quantity
        except CartItem.DoesNotExist:
            total_quantity_after_add = quantity
        
        if total_quantity_after_add > product.stock:
            available_quantity = product.stock - (cart_item.quantity if not created else 0)
            messages.error(request, f"Cannot add {quantity} items. You can only add {available_quantity} more items to your cart.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # Add to cart
        cart_item, created = CartItem.objects.get_or_create(
            cart_id=cart.id, 
            product_id=product.id,  
            defaults={"quantity": quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
            messages.success(request, f"Updated cart: {product.name} quantity increased to {cart_item.quantity}.")
        else:
            messages.success(request, f"Added {quantity} {product.name} to cart.")
            
    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
    except ValueError:
        messages.error(request, "Invalid quantity provided.")
    except Exception as e:
        messages.error(request, "An error occurred while adding to cart.")
    
    return redirect(request.META.get('HTTP_REFERER', '/'))

@role_required("customer", login_url="/login/")
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

@role_required("customer", login_url="/login/")
def user_remove_cart_item(request, id):
    cartitem=CartItem.objects.get(id=id)
    cart=cartitem.cart
    cartitem.delete()
    if not CartItem.objects.filter(cart=cart).exists():
        cart.delete()
    return redirect('user_view_cart')
    
@role_required("customer", login_url="/login/")
def user_add_to_wishlist(request, id):
    user_id=request.user.id
    product_id=id
    if not Wishlist.objects.filter(product_id=product_id, customer_id=user_id):
        Wishlist.objects.create(customer_id=user_id, product_id=product_id)
    return redirect (request.META.get('HTTP_REFERER', '/'))
@role_required("customer", login_url="/login/")    
def user_view_wishlist(request):
    user_id=request.user.id
    wish=Wishlist.objects.filter(customer_id=user_id)

    return render(request, 'user/user_view_wishlist.html', {'wish':wish})

@role_required("customer", login_url="/login/")
def user_remove_wishlist_item(request, id):
    try:
        # Get the wishlist item
        wishlist_item = Wishlist.objects.get(id=id, customer_id=request.user.id)
       
        
        # Delete the wishlist item
        wishlist_item.delete()
        
       
        
        messages.success(request, "Item removed from your wishlist successfully.")
        
    except Wishlist.DoesNotExist:
        messages.error(request, "Wishlist item not found.")
    
    return redirect('user_view_wishlist')

@role_required("customer", login_url="/login/")
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

@role_required("customer", login_url="/login/")
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

@role_required("customer", login_url="/login/")
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

@role_required("customer", login_url="/login/")
def user_cancel_order(request, order_id):
    try:
        # Get the order item by ID and ensure it belongs to the current user
        order_item = OrderItem.objects.get(
            id=order_id, 
            order__customer=request.user  # Changed from order__user to order__customer
        )
        
        # Check if order can be cancelled
        if order_item.order.status in ['pending', 'processing']:  # Note: Capitalized statuses
            # Update order status to cancelled
            order_item.order.status = 'cancelled'  # Note: Capitalized
            order_item.order.save()
            
            messages.success(request, f'Order for {order_item.product_name} has been cancelled successfully.')
        else:
            messages.error(request, 'This order cannot be cancelled.')
            
    except OrderItem.DoesNotExist:
        messages.error(request, 'Order not found or you do not have permission to cancel this order.')
    
    return redirect('user_view_order')

@role_required("customer", login_url="/login/")
def user_add_addresses(request):
    user_id=request.user.id
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



@role_required("customer", login_url="/login/")
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

@role_required("customer", login_url="/login/")
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

@role_required("customer", login_url="/login/")   
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

@role_required("customer", login_url="/login/")
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

@role_required("customer", login_url="/login/")
def user_set_default_address(request):
    address_id = request.POST.get('address_id')
    try:
        # Set all addresses to non-default first
        Address.objects.filter(customer=request.user).update(is_default=False)
        
        # Set the selected address as default
        address = Address.objects.get(id=address_id, customer=request.user)
        address.is_default = True
        address.save()
        
        messages.success(request, 'Default address updated successfully.')
    except Address.DoesNotExist:
        messages.error(request, 'Address not found.')
    
    return redirect('user_add_addresses')


@role_required("customer", login_url="/login/")
def user_delete_address(request):
    address_id = request.POST.get('address_id')
    try:
        address = Address.objects.get(id=address_id, customer=request.user)
        
        # Don't allow deleting the default address if it's the only one
        if address.is_default and Address.objects.filter(customer=request.user).count() == 1:
            messages.error(request, 'Cannot delete your only address. Please add another address first.')
        else:
            address.delete()
            messages.success(request, 'Address deleted successfully.')
            
    except Address.DoesNotExist:
        messages.error(request, 'Address not found.')
    
    return redirect('user_add_addresses')
#--------------------------------------------------------------------------------------------
@role_required("customer", login_url="/login/")
def buy_now_direct(request, product_id):
    try:
        # Get the product
        product = Product.objects.get(id=product_id)
        user_id = request.user.id
        
        # Get quantity from form (default to 1)
        quantity = int(request.POST.get('quantity', 1))
        
        # Validate stock
        if quantity > product.stock:
            messages.error(request, f"Only {product.stock} items available in stock.")
            return redirect('user_view_product_details', id=product_id)
        
        if product.stock <= 0:
            messages.error(request, "This product is out of stock.")
            return redirect('user_view_product_details', id=product_id)
        
        # Get user addresses
        all_addresses = Address.objects.filter(customer_id=user_id)
        default_address = all_addresses.filter(is_default=True).first()
        
        if not default_address and all_addresses.exists():
            default_address = all_addresses.first()
        
        # Calculate totals
        subtotal = product.price * quantity
        shipping = 50  # Same as your cart shipping
        grand_total = subtotal + shipping
        
        context = {
            'product': product,  # Single product for buy now
            'quantity': quantity,
            'cartitems': [],  # Empty list since it's not from cart
            'subtotal': subtotal,
            'shipping': shipping,
            'grand_total': grand_total,
            'user': request.user,
            'customer_profile': getattr(request.user, 'customer_profile', None),
            'address': default_address,
            'all_addresses': all_addresses,
            'is_buy_now': True,  # Flag to identify buy now flow
        }
        
        return render(request, 'user/user_confirm_oder.html', context)
        
    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
        return redirect('user_home')
    except Exception as e:
        messages.error(request, "An error occurred. Please try again.")
        return redirect('user_view_product_details', id=product_id)
    
    
@role_required("customer", login_url="/login/")
def create_buy_now_order(request):
    if request.method == 'POST':
        try:
            user_id = request.user.id
            product_id = request.POST.get('product_id')
            quantity = int(request.POST.get('quantity', 1))
            address_id = request.POST.get('selected_address')
            
            # Get product and validate
            product = Product.objects.get(id=product_id)
            address = Address.objects.get(id=address_id, customer_id=user_id)
            
            # Validate stock
            if quantity > product.stock:
                messages.error(request, f"Only {product.stock} items available in stock.")
                return redirect('user_view_product_details', id=product_id)
            
            # Generate order number
            order_no = generate_order_number()
            total_amount = product.price * quantity
            
            # Create the order
            order = Order.objects.create(
                order_number=order_no, 
                status='pending', 
                total_amount=total_amount, 
                address=address, 
                customer_id=user_id
            )
            
            # Create order item
            OrderItem.objects.create(
                product_name=product.name, 
                product_sku=product.sku, 
                quantity=quantity, 
                price=product.price, 
                order=order, 
                product=product
            )
            
            # Update product stock
            product.stock -= quantity
            product.save()
            
            messages.success(request, f"Order #{order_no} placed successfully!")
            return redirect('user_home')
            
        except (Product.DoesNotExist, Address.DoesNotExist) as e:
            messages.error(request, "Invalid product or address.")
            return redirect('user_home')
        except Exception as e:
            messages.error(request, "An error occurred while processing your order.")
            return redirect('user_home')
#--------------------------------------------------------------------------------------------


@role_required("customer", login_url="/login/")
def create_order(request, id):
    user_id = request.user.id
    address_id = request.POST.get('selected_address')
    cart = Cart.objects.get(id=id, customer_id=user_id)
    cartitems = CartItem.objects.filter(cart_id=cart)
    order_no = generate_order_number()
    tot = 0
    
    # Check stock and adjust quantities if needed
    items_to_order = []
    for item in cartitems:
        available_quantity = min(item.quantity, item.product.stock)
        if available_quantity > 0:
            items_to_order.append({
                'item': item,
                'quantity': available_quantity,
                'subtotal': item.product.price * available_quantity
            })
            tot += item.product.price * available_quantity
    
    if not items_to_order:
        messages.error(request, "No items available for ordering.")
        return redirect('user_view_cart')
    
    # Create the order
    order = Order.objects.create(
        order_number=order_no, 
        status='pending', 
        total_amount=tot, 
        address_id=address_id, 
        customer_id=user_id
    )
    
    # Create order items and update product stock
    for order_item in items_to_order:
        item = order_item['item']
        quantity = order_item['quantity']
        
        OrderItem.objects.create(
            product_name=item.product.name, 
            product_sku=item.product.sku, 
            quantity=quantity, 
            price=item.product.price, 
            order_id=order.id, 
            product_id=item.product.id
        )
        
        # Reduce the product stock
        product = item.product
        product.stock -= quantity
        product.save()
    
    # Delete the cart after order is created
    cart.delete()
    
    messages.success(request, f"Order #{order_no} placed successfully!")
    return redirect('user_home')

@role_required("customer", login_url="/login/")
def user_add_review(request, id):
    product = Product.objects.get(id=id)
    customer = request.user.id

    context = {'product': product}

    if request.method == 'POST':
        # Check duplicate review
        if Review.objects.filter(customer_id=customer, product_id=id).exists():
            messages.error(request, "You have already submitted a review for this product.")
            return redirect('user_view_product_details', id=id)

        review_title = request.POST.get('review_title')
        review_text = request.POST.get('review_text')
        rating = request.POST.get('rating')  # Get the rating from form data
        images = request.FILES.getlist('images')

        # Validate rating
        if not rating or rating == '0':
            messages.error(request, "Please select a rating for the product.")
            return render(request, 'user/user_add_review.html', context)

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                messages.error(request, "Please select a valid rating between 1 and 5 stars.")
                return render(request, 'user/user_add_review.html', context)
        except (ValueError, TypeError):
            messages.error(request, "Invalid rating value.")
            return render(request, 'user/user_add_review.html', context)

        # Create review with rating
        review = Review.objects.create(
            review_title=review_title,
            review_text=review_text,
            rating=rating,  # Add the rating field
            product_id=product.id,
            customer_id=customer
        )

        # Save images
        for image in images:
            ReviewImage.objects.create(review=review, image=image)

        messages.success(request, "Your review has been submitted successfully!")
        return redirect('user_view_product_details', id=id)

    return render(request, 'user/user_add_review.html', context)

import datetime
from django.contrib import messages
import random
from django.shortcuts import render, redirect
from core.models import User
from .models import CustomerProfile, Cart, CartItem, Wishlist, Address, Order, OrderItem, Review, ReviewImage, CustomerNotification
from core.models import Category
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from seller.models import Product, ProductImage, SellerProfile
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decorators.decorators import role_required
from django.shortcuts import get_object_or_404
from seller.models import Notification
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.db.models import Avg

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
    if request.method == 'POST':
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        email = request.POST['email']
        username = request.POST['username']
        phone = request.POST['phone']
        password = request.POST['password']
        confirm_password = request.POST['confirm-password']

        # Password validation
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long!')
            return render(request, 'user/user_reg.html', {
                'firstname': firstname,
                'lastname': lastname,
                'email': email,
                'username': username,
                'phone': phone
            })

        # Username existence check
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists! Please choose a different one.')
            return render(request, 'user/user_reg.html', {
                'firstname': firstname,
                'lastname': lastname,
                'email': email,
                'phone': phone
            })

        # Password match validation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'user/user_reg.html', {
                'firstname': firstname,
                'lastname': lastname,
                'email': email,
                'username': username,
                'phone': phone
            })



        # Email existence check
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists! Please use a different email.')
            return render(request, 'user/user_reg.html', {
                'firstname': firstname,
                'lastname': lastname,
                'username': username,
                'phone': phone
            })

        # Create user if all validations pass
        try:
            user = User.objects.create(
                first_name=firstname, 
                last_name=lastname, 
                email=email, 
                username=username,
                password=make_password(password), 
                role='customer'
            )
            CustomerProfile.objects.create(user=user, phone=phone)
            messages.success(request, 'Registration successful! Please login to continue.')
            return redirect('/login/')
            
        except Exception as e:
            messages.error(request, 'An error occurred during registration. Please try again.')
            return render(request, 'user/user_reg.html')

    return render(request, 'user/user_reg.html')

def login_view(request):
    if request.method == 'POST':
        username=request.POST['username']
        password=request.POST['password']
        
        user=authenticate(username=username, password=password)
        if user is not None and user.role == 'customer':
            login(request, user)
            return redirect('/userhome/')
        else:
             messages.error(request, 'Invalid username or password!')
    return render(request, 'user/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')
    
@role_required("customer", login_url="/login/")
def user_home_view(request):
    return render(request, 'user/user_home.html')



def user_category_view(request):
    categories_list = Category.objects.all()
    paginator = Paginator(categories_list, 6)
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
    products = Product.objects.filter(is_active=True)
    
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
    paginator = Paginator(products, 6)
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
    products_list = Product.objects.filter(category_id=id, is_active =True)
    
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
    product_details = get_object_or_404(Product, id=id, is_active=True)
    images = ProductImage.objects.filter(product=product_details)
    products = Product.objects.filter(is_active=True)
    # Get related products from the same category (excluding current product)
    related_products = Product.objects.filter(
        category=product_details.category,
        is_active=True
    ).exclude(id=product_details.id)[:6]  # Limit to 6 related products
    
    # Check if the current user has already reviewed this product
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = Review.objects.filter(
            customer=request.user, 
            product=product_details
        ).exists()
    average_rating = 0
    reviews = Review.objects.filter(product=product_details)
    if reviews.exists():
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    context = {
        'products':products,
        'product_details': product_details,
        'images': images,
        'user_has_reviewed': user_has_reviewed,
        'related_products': related_products,  # Add related products to context
        'average_rating': average_rating,  # Add average rating to context
        'total_reviews': reviews.count(),
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
            order__customer=request.user
        )
        
        order = order_item.order
        
        # Check if order can be cancelled
        if order.status in ['pending', 'processing']:
            # Update order status to cancelled
            order.status = 'cancelled'
            order.save()
            
           
            try:
                from seller.utils import create_cancellation_notification
                create_cancellation_notification(order, order_item)
                print(f"Cancellation notification created for order #{order.order_number}")
            except Exception as e:
                print(f"Error creating cancellation notification: {e}")
                import traceback
                traceback.print_exc()
            
            # Restore product stock
            try:
                from seller.models import Product
                product = Product.objects.get(id=order_item.product_id)
                product.stock += order_item.quantity
                product.save()
                print(f"Restored {order_item.quantity} units to {product.name} stock")
            except Exception as e:
                print(f"Error restoring product stock: {e}")
            
            messages.success(request, f'Order for {order_item.product_name} has been cancelled successfully.')
        else:
            messages.error(request, 'This order cannot be cancelled as it has already been shipped or delivered.')
            
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
        
        # Get the cart_id or product_id from the form data
        cart_id = request.POST.get('cart_id')
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity')
        is_buy_now = request.POST.get('is_buy_now') == 'true'
        
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

            # Redirect based on the flow
            if is_buy_now and product_id:
                # For buy now flow, redirect to buy now confirmation
                return redirect('user_buy_now_confirm', product_id=product_id, quantity=quantity)
            elif cart_id:
                # For cart flow, redirect back to order confirmation with cart id
                return redirect('user_confirm_order', id=cart_id)
            else:
                # Fallback - redirect to cart
                return redirect('user_view_cart')

        except Exception as e:
            print("ERROR:", e)
            # Fallback redirect
            if cart_id:
                return redirect('user_confirm_order', id=cart_id)
            else:
                return redirect('user_view_cart')

    return redirect('user_view_cart')


@role_required("customer", login_url="/login/")
def user_buy_now_confirm(request, product_id, quantity):
    user_id = request.user.id
    user = User.objects.get(id=user_id)
    customer_profile = CustomerProfile.objects.get(user_id=user_id)
    all_addresses = Address.objects.filter(customer_id=user_id)
    
    try:
        address = Address.objects.get(customer_id=user_id, is_default=True)   
    except Address.DoesNotExist:
        address = Address.objects.filter(customer_id=user_id).first()
    
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    subtotal = product.price * int(quantity)
    shipping = 50
    grand_total = subtotal + shipping
    
    context = {
        'product': product,
        'quantity': quantity,
        'address': address,
        'all_addresses': all_addresses,
        'customer_profile': customer_profile,
        'user': user,
        'subtotal': subtotal,
        'shipping': shipping,
        'grand_total': grand_total,
        'is_buy_now': True
    }
    
    return render(request, 'user/user_confirm_oder.html', context)



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
            payment_method = request.POST.get('payment_method', 'COD')
            
            # Validate inputs
            if not address_id:
                messages.error(request, "Please select a shipping address.")
                return redirect('user_view_product_details', id=product_id)
            
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
                status='Pending', 
                total_amount=total_amount, 
                address=address, 
                customer_id=user_id,
                payment_method=payment_method,
                payment_status='PENDING'
            )
            
            # Create order item
            order_item = OrderItem.objects.create(
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
            
            # Handle payment method
            if payment_method == 'RAZORPAY':
                return redirect('initiate_razorpay_payment', order_id=order.id)
            else:
                # For COD, create notification
                try:
                    from seller.utils import create_order_notification
                    create_order_notification(order, [order_item])
                    print(f"Buy Now notification created for order #{order.order_number}")
                except Exception as e:
                    print(f"Error creating Buy Now notification: {e}")
                
                messages.success(request, f"Order #{order_no} placed successfully! You will pay on delivery.")
                return redirect('order_confirmation', order_id=order.id)
            
        except (Product.DoesNotExist, Address.DoesNotExist) as e:
            messages.error(request, "Invalid product or address.")
            return redirect('user_home')
        except Exception as e:
            print(f"Error in create_buy_now_order: {e}")
            messages.error(request, "An error occurred while processing your order.")
            return redirect('user_home')
#--------------------------------------------------------------------------------------------

@role_required("customer", login_url="/login/")
def create_order(request, id):
    if request.method == 'POST':
        try:
            user_id = request.user.id
            address_id = request.POST.get('selected_address')
            payment_method = request.POST.get('payment_method', 'COD')
            
            # Validate address
            if not address_id:
                messages.error(request, "Please select a shipping address.")
                return redirect('user_view_cart')
            
            cart = Cart.objects.get(id=id, customer_id=user_id)
            cartitems = CartItem.objects.filter(cart_id=cart)
            order_no = generate_order_number()
            tot = 0
            
            # Check stock and adjust quantities if needed
            items_to_order = []
            out_of_stock_items = []
            
            for item in cartitems:
                available_quantity = min(item.quantity, item.product.stock)
                if available_quantity > 0:
                    items_to_order.append({
                        'item': item,
                        'quantity': available_quantity,
                        'subtotal': item.product.price * available_quantity
                    })
                    tot += item.product.price * available_quantity
                else:
                    out_of_stock_items.append(item.product.name)
            
            if not items_to_order:
                messages.error(request, "No items available for ordering.")
                return redirect('user_view_cart')
            
            # Show warning for out-of-stock items
            if out_of_stock_items:
                messages.warning(request, f"Some items were out of stock: {', '.join(out_of_stock_items)}")
            
            # Create the order with payment method
            order = Order.objects.create(
                order_number=order_no, 
                status='Pending',  # Consistent capitalization
                total_amount=tot, 
                address_id=address_id, 
                customer_id=user_id,
                payment_method=payment_method,
                payment_status='PENDING'  # All orders start as pending
            )
            
            # Create order items and update product stock
            order_items = []
            for order_item in items_to_order:
                item = order_item['item']
                quantity = order_item['quantity']
                
                # Create order item
                order_item_obj = OrderItem.objects.create(
                    product_name=item.product.name, 
                    product_sku=item.product.sku, 
                    quantity=quantity, 
                    price=item.product.price, 
                    order_id=order.id, 
                    product_id=item.product.id
                )
                order_items.append(order_item_obj)
                
                # Reduce the product stock
                product = item.product
                product.stock -= quantity
                product.save()
            
            # Handle payment method
            if payment_method == 'RAZORPAY':
                # For Razorpay, don't delete cart yet (in case payment fails)
                # Redirect to Razorpay payment page
                return redirect('initiate_razorpay_payment', order_id=order.id)
            else:
                # For COD, payment is considered pending until delivery
                # Create notification and complete the order process
                try:
                    from seller.utils import create_order_notification
                    create_order_notification(order, order_items)
                    print(f"WebSocket notifications created for order #{order.order_number}")
                except Exception as e:
                    print(f"Error creating notifications: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Delete the cart after successful COD order creation
                cart.delete()
                
                messages.success(request, f"Order #{order_no} placed successfully! You will pay on delivery.")
                return redirect('order_confirmation', order_id=order.id)
                
        except Cart.DoesNotExist:
            messages.error(request, "Cart not found.")
            return redirect('user_view_cart')
        except Address.DoesNotExist:
            messages.error(request, "Invalid shipping address.")
            return redirect('user_view_cart')
        except Exception as e:
            print(f"Error creating order: {e}")
            import traceback
            traceback.print_exc()
            messages.error(request, "An error occurred while processing your order.")
            return redirect('user_view_cart')
    
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
        rating = request.POST.get('rating')
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
            rating=rating,
            product_id=product.id,
            customer_id=customer
        )

        # Save images
        for image in images:
            ReviewImage.objects.create(review=review, image=image)

       
        try:
            from seller.utils import create_review_notification
            create_review_notification(review)
            print(f"Review notification created for {product.name}")
        except Exception as e:
            print(f"Error creating review notification: {e}")
            import traceback
            traceback.print_exc()

        messages.success(request, "Your review has been submitted successfully!")
        return redirect('user_view_product_details', id=id)

    return render(request, 'user/user_add_review.html', context)


@role_required("customer", login_url="/login/")
def order_details(request, order_id):
    """View for order details page"""
    # Get order and check if it belongs to the current user
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    
    # Get order items for this order
    order_items = order.items.all()
    
    # Mark related notifications as read
    Notification.objects.filter(
        customer=request.user,
        order=order,
        is_read=False
    ).update(is_read=True)
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'user/order_details.html', context)

@role_required("customer", login_url="/login/")
def product_details(request, product_id):
    """View for product details page (with reviews)"""
    product = get_object_or_404(Product, id=product_id, is_listed=True)
    
    # Get reviews for this product
    reviews = Review.objects.filter(product=product).select_related('customer')
    
    # Mark related notifications as read
    Notification.objects.filter(
        customer=request.user,
        review__product=product,
        is_read=False
    ).update(is_read=True)
    
    context = {
        'product': product,
        'reviews': reviews,
    }
    
    return render(request, 'user/product_details.html', context)



from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
def get_notification_icon(notification_type):
    """Get appropriate icon for notification type"""
    icon_map = {
        'order_placed': 'fas fa-shopping-bag',
        'order_confirmed': 'fas fa-check-circle',
        'order_shipped': 'fas fa-shipping-fast',
        'order_delivered': 'fas fa-box-open',
        'order_cancelled': 'fas fa-times-circle',
        'seller_reply': 'fas fa-reply',
        'promotion': 'fas fa-tag',
        'info': 'fas fa-info-circle'
    }
    return icon_map.get(notification_type, 'fas fa-bell')

@login_required
def get_user_notifications(request):
    """Get all notifications for the current user"""
    notifications = CustomerNotification.objects.filter(user=request.user).order_by('-created_at')[:50]
    
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'created_at': notification.created_at.isoformat(),
            'is_read': notification.is_read,
            'order_id': notification.order.id if notification.order else None
        })
    
    return JsonResponse({'notifications': notifications_data})

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = CustomerNotification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except CustomerNotification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})

@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current user"""
    CustomerNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
def get_unread_notification_count(request):
    """Get count of unread notifications"""
    count = CustomerNotification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})



from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def user_all_notifications(request):
    """User notifications page"""
    # Get all notifications for the current user
    notifications = CustomerNotification.objects.filter(user=request.user).order_by('-created_at')
    
    # Get counts
    total_count = notifications.count()
    unread_count = notifications.filter(is_read=False).count()
    read_count = total_count - unread_count
    
    # Add icons to each notification
    for notification in notifications:
        notification.icon = get_notification_icon(notification.notification_type)
    
    # Pagination
    paginator = Paginator(notifications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'unread_count': unread_count,
        'read_count': read_count,
    }
    
    return render(request, 'user/customer_all_notifications.html', context)

@login_required
def clear_single_notification(request, notification_id):
    """Clear a single notification"""
    try:
        notification = CustomerNotification.objects.get(id=notification_id, user=request.user)
        notification.delete()
        return JsonResponse({'success': True})
    except CustomerNotification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})

import razorpay
import os
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Order, OrderItem, Cart
from decorators.decorators import role_required

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get Razorpay keys from environment
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')

# Initialize Razorpay client
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

@role_required("customer", login_url="/login/")
def initiate_razorpay_payment(request, order_id):
    """
    1. Creates Razorpay order
    2. Shows payment page
    """
    try:
        order = Order.objects.get(id=order_id, customer=request.user)
        
        razorpay_order = client.order.create({
             'amount': int((order.total_amount + 50) * 100),
            'currency': 'INR',
            'payment_capture': 1,
        })
        
        order.razorpay_order_id = razorpay_order['id']
        order.save()
        amt=order.total_amount+50
        context = {
            'order': order,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': RAZORPAY_KEY_ID,
            'amount': order.total_amount+50,
            'currency': 'INR',
            'user': {
                'name': f"{request.user.first_name} {request.user.last_name}",
                'email': request.user.email,
                'phone': getattr(request.user.customer_profile, 'phone', '')
            }
        }
        
        return render(request, 'user/payment.html', context)
        
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('user_home')
    except Exception as e:
        print(f"Error initiating Razorpay payment: {e}")
        messages.error(request, "Error initiating payment. Please try again.")
        return redirect('user_home')

@csrf_exempt
def razorpay_payment_success(request):
    """
    3. Handles successful payment callback
    """
    if request.method == "POST":
        try:
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            
            # Verify payment signature
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            client.utility.verify_payment_signature(params_dict)
            
            # Update order status
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.payment_status = 'PAID'
            order.save()
            
            # Create notification
            order_items = OrderItem.objects.filter(order=order)
            try:
                from seller.utils import create_order_notification
                create_order_notification(order, list(order_items))
            except Exception as e:
                print(f"Error creating notification: {e}")
            
            # Delete cart
            try:
                cart = Cart.objects.get(customer=request.user)
                cart.delete()
            except Cart.DoesNotExist:
                pass
            
            messages.success(request, f"Payment successful! Order #{order.order_number} confirmed.")
            return redirect('order_confirmation', order_id=order.id)
            
        except Order.DoesNotExist:
            messages.error(request, "Order not found.")
            return redirect('user_home')
        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "Payment verification failed.")
            return redirect('payment_failed')
        except Exception as e:
            print(f"Payment success error: {e}")
            messages.error(request, "Payment processing error.")
            return redirect('payment_failed')
    
    return redirect('user_home')

def payment_failed(request):
    """
    4. Shows payment failed page
    """
    messages.error(request, "Payment failed. Please try again.")
    return redirect('user_view_cart')

def order_confirmation(request, order_id):
    """
    5. Shows order confirmation page
    """
    try:
        order = Order.objects.get(id=order_id, customer=request.user)
        order_items = OrderItem.objects.filter(order=order)
        total_with_shipping = order.total_amount + 50
        context = {
            'order': order,
            'order_items': order_items,
             'amount': total_with_shipping, 
        }
        
        return render(request, 'user/order_confirmation.html', context)
        
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('user_home')
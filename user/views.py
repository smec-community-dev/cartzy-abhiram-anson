from django.shortcuts import render, redirect
from core.models import User
from .models import CustomerProfile
from core.models import Category
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from seller.models import Product

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
    products=Product.objects.filter(id = id)
    return render(request, 'user/user_view_products.html', {'products':products})
from django.urls import path
from .import views

urlpatterns=[
    path('', views.home_view, name='home'),
    path('About', views.about_view, name='about_us'),
    path('UserReg/', views.user_reg_view, name='/register/'),
    path('login/', views.login_view, name='/login/'),
    path('logout/', views.logout_view, name='/logout/'),
    path('userhome/', views.user_home_view),
    
    
    path('categories/', views.user_category_view, name='user_view_category'),
    path('viewproducts/<int:id>/', views.user_products_view, name='user_view_products'),
    
    
    
    
]
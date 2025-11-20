from django.urls import path
from .import views

urlpatterns=[
    path('', views.home_view, name='home'),
    path('About', views.about_view, name='about_us'),
    path('UserReg/', views.user_reg_view, name='/register/'),
    path('login/', views.login_view, name='/login/'),
    path('logout/', views.logout_view, name='/logout/'),
    
    path('userhome/', views.user_home_view, name='user_home'),
    
    
    path('categories/', views.user_category_view, name='user_view_category'),
    path('allproducts/', views.user_view_all_products, name='user_view_all_products'),
    path('products/<int:id>/', views.user_view_products, name='user_view_products'),
    path('productdetails/<int:id>/', views.user_view_product_details, name='user_view_product_details'),
    
    
    path('addtocart/<int:id>/', views.user_add_to_cart, name='user_add_to_cart'),
    path('removecartitem/<int:id>/', views.user_remove_cart_item, name='user_remove_cart_item'),
    path('viewcart', views.user_view_cart, name='user_view_cart'),
    
    path('wishlist/', views.user_view_wishlist, name='user_view_wishlist'),
    path('addtowishlist/<int:id>/', views.user_add_to_wishlist, name='user_add_to_wishlist'),
    
    path('useraccount', views.user_view_account, name='user_view_account' ),
    path('userupdateaccount', views.user_update_account, name='user_update_account' ),
    
    path('userconfirmorder/<int:id>/', views.user_confirm_order, name='user_confirm_order'),
    # path('usercheckout/<int:id>/', views.user_proceed_to_checkout, name='user_proceed_to_checkout'),
    
    
    
    path('uservieworder', views.user_view_order, name='user_view_order'),
    path('useraddaddress', views.user_add_addresses, name='user_add_addresses'),
    
    path('useraddaddress', views.user_add_addresses, name='user_add_new_address'),
    path('useraddanaddress', views.user_add_new_address, name='user_add_an_address'),
    path('userchooseaddress/<int:id>/', views.user_choose_address, name='user_choose_address'),
    path('uupdateaddress', views.user_update_order_address, name='user_update_order_address'),
    
    path('userorder/<int:id>/', views.create_order, name='user_create_order'),
    
    
    path('useraddreview/<int:id>/', views.user_add_review, name='user_add_review'),
    
    
]
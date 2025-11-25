from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    # Admin Dashboard URLs
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
        path('admin/notifications/', views.admin_notifications, name='admin_notifications'),
        
        # Admin API Endpoints
        path('admin/api/sellers/<int:seller_id>/verify/', views.verify_seller, name='verify_seller'),
        path('admin/api/users/<int:user_id>/deactivate/', views.deactivate_user, name='deactivate_user'),
        path('admin/api/users/<int:user_id>/activate/', views.activate_user, name='activate_user'),
        
        # Admin Management Pages
        path('admin/users/', views.admin_users, name='admin_users'),
        path('admin/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
        path('admin/sellers/', views.admin_sellers, name='admin_sellers'),
        path('admin/sellers/<int:seller_id>/', views.admin_seller_detail, name='admin_seller_detail'),
        path('admin/products/', views.admin_products, name='admin_products'),
        path('admin/products/<int:product_id>/', views.admin_product_detail, name='admin_product_detail'),
        path('admin/orders/', views.admin_orders, name='admin_orders'),
        path('admin/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
        path('admin/categories/', views.admin_categories, name='admin_categories'),
        path('admin/categories/<int:category_id>/', views.admin_category_detail, name='admin_category_detail'),
        path('admin/reviews/', views.admin_reviews, name='admin_reviews'),
        path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
        path('admin/settings/', views.admin_settings, name='admin_settings'),
        
        # Home & Public Pages
        path('', views.home, name='home'),
        path('about/', views.about, name='about'),
        path('contact/', views.contact, name='contact'),
        path('privacy/', views.privacy_policy, name='privacy_policy'),
        path('terms/', views.terms_of_service, name='terms_of_service'),
        
        # Authentication (if not handled by user app)
        path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
        path('logout/', auth_views.LogoutView.as_view(), name='logout'),
 ]
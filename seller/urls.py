from django.urls import path
from . import views
app_name='seller'
urlpatterns = [
    path("register/", views.seller_register, name= "seller_register"),
    path("login/", views.seller_login, name="seller_login"),
    path("dashboard/", views.seller_dashboard, name="seller_dashboard"),
    path("addproduct/", views.add_product, name="add_product"),
    path("update/<int:product_id>/", views.update_product, name="update_product"),
    path("delete/<int:product_id>", views.delete_product, name="delete_product"),
    path("products/", views.seller_products, name="seller_products"),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('orders/', views.seller_orders, name='seller_orders'),
    path('profile/', views.seller_profile, name='seller_profile'),
    path('reviews/', views.seller_reviews, name='seller_reviews'),
    # path('reviews/<int:review_id>/reply/', views.reply_to_review, name='reply_to_review'),
    path('orders/<int:order_id>/details/', views.order_details, name='order_details'),
    path('notifications/', views.all_notifications, name='all_notifications'),
    path('notifications/<int:notification_id>/clear/', views.clear_notification, name='clear_notification'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('reviews/<int:review_id>/reply/', views.add_seller_reply, name='add_seller_reply'),
  
]

from django.urls import path
from . import views

urlpatterns = [
    path("seller/register/", views.seller_register),
    path("seller/login/", views.seller_login),
    path("seller/dashboard/", views.seller_dashboard),
    path("seller/addproduct/", views.add_product),
]

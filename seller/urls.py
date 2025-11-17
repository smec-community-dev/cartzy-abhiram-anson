from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.seller_register),
    path("login/", views.seller_login),
    path("dashboard/", views.seller_dashboard),
    path("addproduct/", views.add_product),
]

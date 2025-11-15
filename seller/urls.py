from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.seller_register, name="seller_register"),
    path("login/", views.seller_login, name="seller_login"),
    path("dashboard/", views.seller_dashboard, name="seller_dashboard"),
    path("product/add/", views.add_product, name="add_product"),
]

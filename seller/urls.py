from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.seller_register),
    path("login/", views.seller_login),
    path("dashboard/", views.seller_dashboard),
    path("addproduct/", views.add_product),
    path("update/<int:product_id>/", views.update_product, name="update_product"),
    path("delete/<int:product_id>", views.delete_product, name="delete_product"),
]

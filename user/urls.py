from django.urls import path
from .import views

urlpatterns=[
    path('UserReg/', views.user_reg_view),
    path('login/', views.login_view),
    path('customerhome/', views.user_home_view),
    
]
from django.urls import path
from .import views

urlpatterns=[
    path('', views.home_view, name='home'),
    path('About', views.about_view, name='about_us'),
    path('UserReg/', views.user_reg_view),
    path('login/', views.login_view, name='login/'),
    path('customerhome/', views.user_home_view),
    
]
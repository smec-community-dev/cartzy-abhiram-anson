from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from user.views import set_google_customer, set_google_seller, role_redirect



urlpatterns = [
    path('admin/', admin.site.urls),

    path('core/', include('core.urls')),
    path('seller/', include('seller.urls', namespace='seller')),
    path('', include('user.urls')),

    
    path("role-redirect/", role_redirect, name="role_redirect"),

   
    path("accounts/", include("allauth.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

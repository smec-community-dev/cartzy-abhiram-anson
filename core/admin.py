from django.contrib import admin
from .models import Category, User

admin.site.register(User)

@admin.register(Category)
class CatAdmin(admin.ModelAdmin):
    list_display=('name', 'description', 'image')
    

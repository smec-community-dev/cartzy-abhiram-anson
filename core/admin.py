from django.contrib import admin
from .models import Category

@admin.register(Category)
class CatAdmin(admin.ModelAdmin):
    list_display=('name', 'description', 'image')
    

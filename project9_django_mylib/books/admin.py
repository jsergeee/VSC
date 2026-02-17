from django.contrib import admin
from .models import Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'year', 'is_read', 'created_at')
    list_filter = ('is_read', 'year', 'author')
    search_fields = ('title', 'author')
    ordering = ('-created_at',)
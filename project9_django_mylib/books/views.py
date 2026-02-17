from django.shortcuts import render
from .models import Book

def book_list(request):
    # Получаем все книги из базы данных
    books = Book.objects.all().order_by('-created_at')
    
    # Передаем книги в шаблон
    return render(request, 'books/book_list.html', {'books': books})
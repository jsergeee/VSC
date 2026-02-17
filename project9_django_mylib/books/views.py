from django.shortcuts import render, get_object_or_404
from .models import Book

def book_list(request):
    # Получаем параметры фильтрации из запроса
    author_filter = request.GET.get('author', '')
    year_filter = request.GET.get('year', '')
    read_filter = request.GET.get('read', '')
    
    books = Book.objects.all().order_by('-created_at')
    
        # Поиск по названию
    search_query = request.GET.get('search', '')
    if search_query:
        books = books.filter(title__icontains=search_query) | books.filter(author__icontains=search_query)
    
    # Применяем фильтры
    if author_filter:
        books = books.filter(author__icontains=author_filter)
    if year_filter:
        books = books.filter(year=year_filter)
    if read_filter:
        is_read = read_filter == 'read'
        books = books.filter(is_read=is_read)
    
    # Получаем уникальных авторов и года для фильтров
    authors = Book.objects.values_list('author', flat=True).distinct()
    years = Book.objects.values_list('year', flat=True).distinct().order_by('-year')
    
    context = {
        'books': books,
        'authors': authors,
        'years': years,
        'current_author': author_filter,
        'current_year': year_filter,
        'current_read': read_filter,
        'search_query': search_query,
    }
    return render(request, 'books/book_list.html', context)

def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    return render(request, 'books/book_detail.html', {'book': book})
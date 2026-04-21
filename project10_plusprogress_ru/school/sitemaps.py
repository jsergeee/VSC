# school/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Article

class StaticSitemap(Sitemap):
    """Статические страницы"""
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return [
            '/',
            '/articles/',
            '/team/',
        ]

    def location(self, item):
        return item

    def priority(self, item):
        if item == '/':
            return 1.0
        elif item == '/articles/':
            return 0.9
        return 0.8


class ArticleSitemap(Sitemap):
    """Динамические страницы статей"""
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Article.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('article_detail', kwargs={'slug': obj.slug})


class TeacherSitemap(Sitemap):
    """Страницы преподавателей (опционально)"""
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        from .models import Teacher
        return Teacher.objects.filter(user__is_active=True)

    def location(self, obj):
        return reverse('teacher_detail', kwargs={'teacher_id': obj.id})
"""
URL configuration for plusprogress project.
"""
# plusprogress/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('school.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('school.api_urls')),
    path('docs/', include('django_mkdocs.urls')),
]

# ВСЕ добавления статических и медиа файлов ТОЛЬКО внутри DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.shortcuts import render
from .models import Event

class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'date')
    search_fields = ('title',)
    
    @method_decorator(staff_member_required)
    @method_decorator(never_cache)
    def changelist_view(self, request, extra_context=None):
        # Если запрошен календарь
        if request.GET.get('view') == 'calendar':
            events = self.get_queryset(request)
            extra_context = extra_context or {}
            extra_context['events'] = events
            extra_context['title'] = 'Календарь событий'
            
            return render(request, 'admin/events/event/change_list_calendar.html', extra_context)
        
        # Обычный список
        return super().changelist_view(request, extra_context)

# Только ОДИН способ регистрации! Уберите @admin.register
admin.site.register(Event, EventAdmin)
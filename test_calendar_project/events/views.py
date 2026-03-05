from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import Event

@staff_member_required
def event_calendar(request):
    events = Event.objects.all()
    return render(request, 'admin/events/event/change_list.html', {
        'events': events
    })
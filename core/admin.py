from django.contrib import admin
from .models import Session, Semester, NewsAndEvents


class NewsAndEventsAdmin(admin.ModelAdmin):
    list_display = ('title', 'posted_as', 'event_date', 'updated_date')
    list_filter = ('posted_as', 'event_date')
    search_fields = ('title', 'summary', 'posted_as')
    ordering = ('-updated_date',)
    readonly_fields = ('upload_time', 'updated_date')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


admin.site.register(Semester)
admin.site.register(Session)
admin.site.register(NewsAndEvents, NewsAndEventsAdmin)

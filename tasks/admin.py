from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'status',
        'priority',
        'progress',
        'due_date',
        'is_pinned',
        'created_at',
    )
    list_filter = ('status', 'priority', 'is_pinned', 'due_date')
    search_fields = ('title', 'description', 'user__username')
    list_editable = ('status', 'priority', 'progress', 'is_pinned')
    ordering = ('-created_at',)

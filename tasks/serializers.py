from rest_framework import serializers

from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'priority',
            'progress',
            'due_date',
            'is_pinned',
            'is_overdue',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('created_at', 'updated_at', 'is_overdue')


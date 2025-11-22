from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Task(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not started'
        IN_PROGRESS = 'in_progress', 'In progress'
        BLOCKED = 'blocked', 'Blocked'
        COMPLETED = 'completed', 'Completed'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks',
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    progress = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Completion percentage (0-100%).',
    )
    due_date = models.DateField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', 'status', 'due_date', 'priority', '-created_at']

    def __str__(self) -> str:
        return self.title

    @property
    def is_overdue(self) -> bool:
        if not self.due_date or self.status == self.Status.COMPLETED:
            return False
        return self.due_date < timezone.localdate()

    def save(self, *args, **kwargs):
        if self.status == self.Status.COMPLETED:
            self.progress = 100
        elif self.progress == 100 and self.status != self.Status.COMPLETED:
            self.status = self.Status.IN_PROGRESS
        self.progress = max(0, min(100, self.progress))
        super().save(*args, **kwargs)


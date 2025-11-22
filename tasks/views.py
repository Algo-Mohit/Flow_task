from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework import permissions, viewsets

from .forms import TaskForm, UserRegistrationForm
from .models import Task
from .serializers import TaskSerializer


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome aboard! Your workspace is ready.')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/signup.html', {'form': form})


@login_required
def dashboard(request):
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '').strip()

    user_tasks = Task.objects.filter(user=request.user)
    tasks = user_tasks

    valid_statuses = set(Task.Status.values)
    if status_filter not in valid_statuses and status_filter != 'all':
        status_filter = 'all'

    if status_filter != 'all':
        tasks = tasks.filter(status=status_filter)

    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    tasks = tasks.order_by('-is_pinned', 'due_date', 'title')

    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(status=Task.Status.COMPLETED).count()
    in_progress_tasks = user_tasks.filter(status=Task.Status.IN_PROGRESS).count()
    blocked_tasks = user_tasks.filter(status=Task.Status.BLOCKED).count()
    overdue_tasks = user_tasks.filter(
        due_date__lt=timezone.localdate()
    ).exclude(status=Task.Status.COMPLETED).count()

    overall_progress = round((completed_tasks / total_tasks) * 100) if total_tasks else 0
    upcoming = user_tasks.filter(due_date__gte=timezone.localdate()).order_by('due_date')[:3]

    context = {
        'tasks': tasks,
        'status_filter': status_filter,
        'search_query': search_query,
        'summary': {
            'total': total_tasks,
            'completed': completed_tasks,
            'in_progress': in_progress_tasks,
            'blocked': blocked_tasks,
            'overdue': overdue_tasks,
            'overall_progress': overall_progress,
        },
        'upcoming': upcoming,
    }
    return render(request, 'tasks/dashboard.html', context)


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, 'Task created successfully.')
            return redirect('dashboard')
    else:
        form = TaskForm()

    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Create task'})


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully.')
            return redirect('dashboard')
    else:
        form = TaskForm(instance=task)

    return render(
        request,
        'tasks/task_form.html',
        {'form': form, 'title': 'Update task', 'task': task},
    )


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)

    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task removed.')
        return redirect('dashboard')

    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
@require_POST
def toggle_pin(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.is_pinned = not task.is_pinned
    task.save()
    return redirect('dashboard')


@login_required
@require_POST
def update_status(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    new_status = request.POST.get('status')

    if new_status in Task.Status.values:
        task.status = new_status
        if new_status == Task.Status.COMPLETED:
            task.progress = 100
        task.save()
        messages.success(request, f'Task marked as {task.get_status_display().lower()}.')
    else:
        messages.error(request, 'Invalid status update.')

    return redirect('dashboard')


class IsOwner(permissions.BasePermission):
    """Ensure API callers only access their own tasks."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        qs = Task.objects.filter(user=self.request.user)
        status_filter = self.request.query_params.get('status')
        if status_filter in Task.Status.values:
            qs = qs.filter(status=status_filter)
        search_query = self.request.query_params.get('q')
        if search_query:
            qs = qs.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
            )
        return qs.order_by('-is_pinned', 'due_date', 'title')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

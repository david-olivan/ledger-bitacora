from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST, require_http_methods

from .forms import ProjectForm, TaskForm
from .models import Bucket, ChecklistItem, Project, Tag, Task, TaskTag


def _annotated_projects(user):
    return Project.objects.filter(owner=user).annotate(
        total_tasks=Count('buckets__tasks', distinct=True),
        done_tasks=Count('buckets__tasks', filter=Q(buckets__tasks__completed=True), distinct=True),
        bucket_count=Count('buckets', distinct=True),
    )


def _get_bucket_with_tasks(bucket_pk):
    active_qs = Task.objects.filter(completed=False).order_by('position', 'created_at').prefetch_related('task_tags__tag', 'checklist_items')
    completed_qs = Task.objects.filter(completed=True).order_by('completed_at').prefetch_related('task_tags__tag', 'checklist_items')
    return Bucket.objects.prefetch_related(
        Prefetch('tasks', queryset=active_qs, to_attr='active_tasks'),
        Prefetch('tasks', queryset=completed_qs, to_attr='completed_tasks'),
    ).get(pk=bucket_pk)


@login_required
def project_list(request):
    projects = _annotated_projects(request.user)
    form = ProjectForm()
    return render(request, 'workbench/project_list.html', {'projects': projects, 'form': form})


@login_required
@require_POST
def project_create(request):
    form = ProjectForm(request.POST)
    if form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        Bucket.objects.create(project=project, name=_('En progreso'), order=0)
        return redirect('workbench:project_list')
    projects = _annotated_projects(request.user)
    return render(request, 'workbench/project_list.html', {'projects': projects, 'form': form})


@login_required
@require_POST
def project_pin(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if project.pinned:
        project.pinned = False
        project.pin_order = None
        project.save()
    else:
        count = Project.objects.filter(owner=request.user, pinned=True).count()
        if count < 5:
            max_order = Project.objects.filter(owner=request.user, pinned=True).aggregate(m=Max('pin_order'))['m'] or 0
            project.pinned = True
            project.pin_order = max_order + 1
            project.save()
    return redirect('workbench:project_list')


@login_required
@require_POST
def project_delete(request, pk):
    get_object_or_404(Project, pk=pk, owner=request.user).delete()
    return redirect('workbench:project_list')


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    active_view = request.GET.get('view', 'buckets')
    active_qs = Task.objects.filter(completed=False).order_by('position', 'created_at').prefetch_related('task_tags__tag', 'checklist_items')
    completed_qs = Task.objects.filter(completed=True).order_by('completed_at').prefetch_related('task_tags__tag', 'checklist_items')
    buckets = project.buckets.prefetch_related(
        Prefetch('tasks', queryset=active_qs, to_attr='active_tasks'),
        Prefetch('tasks', queryset=completed_qs, to_attr='completed_tasks'),
    )
    return render(request, 'workbench/project_detail.html', {'project': project, 'buckets': buckets, 'active_view': active_view})


@login_required
@require_POST
def task_create(request, bucket_pk):
    bucket = get_object_or_404(Bucket, pk=bucket_pk, project__owner=request.user)
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.bucket = bucket
        max_pos = bucket.tasks.aggregate(m=Max('position'))['m'] or 0
        task.position = max_pos + 1
        task.save()
        return render(request, 'workbench/partials/task_card.html', {'task': task})
    return HttpResponse(status=422)


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk, bucket__project__owner=request.user)
    form = TaskForm(instance=task)
    tags = task.bucket.project.tags.all()
    task_tag_ids = list(task.task_tags.values_list('tag_id', flat=True))
    checklist_items = task.checklist_items.all()
    return render(request, 'workbench/partials/task_editor.html', {
        'task': task,
        'form': form,
        'tags': tags,
        'task_tag_ids': task_tag_ids,
        'checklist_items': checklist_items,
    })


@login_required
@require_POST
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, bucket__project__owner=request.user)
    form = TaskForm(request.POST, instance=task)
    if form.is_valid():
        form.save()
        tag_ids = request.POST.getlist('tags')
        task.task_tags.all().delete()
        for tag_id in tag_ids[:3]:
            try:
                tag = Tag.objects.get(pk=tag_id, project=task.bucket.project)
                TaskTag.objects.create(task=task, tag=tag)
            except Tag.DoesNotExist:
                pass
        task.refresh_from_db()
        return render(request, 'workbench/partials/task_card.html', {'task': task})
    tags = task.bucket.project.tags.all()
    task_tag_ids = list(task.task_tags.values_list('tag_id', flat=True))
    checklist_items = task.checklist_items.all()
    return render(request, 'workbench/partials/task_editor.html', {
        'task': task,
        'form': form,
        'tags': tags,
        'task_tag_ids': task_tag_ids,
        'checklist_items': checklist_items,
    })


@login_required
@require_http_methods(['DELETE'])
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, bucket__project__owner=request.user)
    task.delete()
    return HttpResponse(status=200)


@login_required
@require_POST
def task_complete(request, pk):
    task = get_object_or_404(Task, pk=pk, bucket__project__owner=request.user)
    task.completed = not task.completed
    task.completed_at = timezone.now() if task.completed else None
    task.save()
    bucket = _get_bucket_with_tasks(task.bucket_id)
    return render(request, 'workbench/partials/bucket_column.html', {'bucket': bucket})


@login_required
@require_POST
def checklist_item_add(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk, bucket__project__owner=request.user)
    text = request.POST.get('text', '').strip()
    if text:
        max_pos = task.checklist_items.aggregate(m=Max('position'))['m'] or 0
        item = ChecklistItem.objects.create(task=task, text=text, position=max_pos + 1)
        return render(request, 'workbench/partials/checklist_item.html', {'item': item})
    return HttpResponse(status=422)


@login_required
@require_POST
def checklist_item_toggle(request, pk):
    item = get_object_or_404(ChecklistItem, pk=pk, task__bucket__project__owner=request.user)
    item.checked = not item.checked
    item.save()
    return render(request, 'workbench/partials/checklist_item.html', {'item': item})


@login_required
@require_http_methods(['DELETE'])
def checklist_item_delete(request, pk):
    item = get_object_or_404(ChecklistItem, pk=pk, task__bucket__project__owner=request.user)
    item.delete()
    return HttpResponse(status=200)

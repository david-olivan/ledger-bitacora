import calendar as _cal
from datetime import date as _date

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
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


def _get_calendar_context(request, project):
    today = _date.today()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        if not (1 <= month <= 12):
            month = today.month
    except (ValueError, TypeError):
        year, month = today.year, today.month

    _, days_in_month = _cal.monthrange(year, month)
    period_start = _date(year, month, 1)
    period_end = _date(year, month, days_in_month)

    tasks = (
        Task.objects.filter(bucket__project=project, completed=False)
        .exclude(start_date__isnull=True, end_date__isnull=True)
        .filter(
            Q(start_date__lte=period_end) | Q(start_date__isnull=True),
            Q(end_date__gte=period_start) | Q(end_date__isnull=True),
        )
        .select_related('bucket')
        .prefetch_related('task_tags__tag')
        .order_by('start_date', 'end_date', 'created_at')
    )

    gantt_tasks = []
    for task in tasks:
        start = task.start_date or task.end_date
        end = task.end_date or task.start_date
        bar_start = max(start, period_start)
        bar_end = min(end, period_end)
        if bar_start > bar_end:
            continue
        tt_list = list(task.task_tags.all())
        color = tt_list[0].tag.color if tt_list else 'brass'
        left_pct = round((bar_start.day - 1) / days_in_month * 100, 2)
        width_pct = round((bar_end.day - bar_start.day + 1) / days_in_month * 100, 2)
        gantt_tasks.append({
            'task': task,
            'color': color,
            'bar_left_pct': left_pct,
            'bar_width_pct': width_pct,
            'bucket_name': task.bucket.name,
        })

    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    return {
        'gantt_year': year,
        'gantt_month': month,
        'gantt_month_name': _cal.month_name[month],
        'gantt_days': list(range(1, days_in_month + 1)),
        'gantt_tasks': gantt_tasks,
        'gantt_prev': f'?view=calendar&year={prev_year}&month={prev_month}',
        'gantt_next': f'?view=calendar&year={next_year}&month={next_month}',
        'gantt_today': today,
    }


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
        Bucket.objects.create(project=project, name=_('In Progress'), order=0)
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
    ctx = {'project': project, 'buckets': buckets, 'active_view': active_view}
    if active_view == 'calendar':
        ctx.update(_get_calendar_context(request, project))
    return render(request, 'workbench/project_detail.html', ctx)


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
        return render(request, 'workbench/partials/bucket_column.html', {'bucket': _get_bucket_with_tasks(bucket.pk)})
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


@login_required
@require_POST
def task_reorder(request):
    task_id = request.POST.get('task_id')
    bucket_id = request.POST.get('bucket_id')
    try:
        new_pos = int(request.POST.get('position', 0))
    except (ValueError, TypeError):
        new_pos = 0

    task = get_object_or_404(Task, pk=task_id, bucket__project__owner=request.user)
    new_bucket = get_object_or_404(Bucket, pk=bucket_id, project=task.bucket.project)
    old_bucket_id = task.bucket_id

    others = list(
        Task.objects.filter(bucket=new_bucket, completed=False)
        .exclude(pk=task.pk)
        .order_by('position', 'created_at')
    )
    others.insert(new_pos, task)
    for i, t in enumerate(others):
        Task.objects.filter(pk=t.pk).update(bucket=new_bucket, position=i)

    if old_bucket_id != new_bucket.pk:
        for i, t in enumerate(
            Task.objects.filter(bucket_id=old_bucket_id, completed=False).order_by('position', 'created_at')
        ):
            Task.objects.filter(pk=t.pk).update(position=i)

    return HttpResponse(status=200)


@login_required
def project_tags(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    tags = project.tags.all().order_by('color')
    used_colors = set(tags.values_list('color', flat=True))
    available_colors = [(c, label) for c, label in Tag.Color.choices if c not in used_colors]
    return render(request, 'workbench/project_tags.html', {
        'project': project,
        'tags': tags,
        'available_colors': available_colors,
    })


@login_required
@require_POST
def tag_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk, owner=request.user)
    name = request.POST.get('name', '').strip()
    color = request.POST.get('color', '')
    valid_colors = dict(Tag.Color.choices)
    if name and color in valid_colors:
        try:
            Tag.objects.create(project=project, name=name, color=color)
        except IntegrityError:
            pass
    return redirect('workbench:project_tags', pk=project.pk)


@login_required
@require_POST
def tag_update(request, pk):
    tag = get_object_or_404(Tag, pk=pk, project__owner=request.user)
    name = request.POST.get('name', '').strip()
    if name:
        tag.name = name
        tag.save(update_fields=['name'])
    return redirect('workbench:project_tags', pk=tag.project_id)


@login_required
@require_POST
def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk, project__owner=request.user)
    project_pk = tag.project_id
    tag.delete()
    return redirect('workbench:project_tags', pk=project_pk)

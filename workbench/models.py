from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Project(models.Model):
    name = models.CharField(_('name'), max_length=255)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='projects', verbose_name=_('owner'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pinned = models.BooleanField(_('pinned'), default=False)
    pin_order = models.PositiveSmallIntegerField(_('pin order'), null=True, blank=True)

    class Meta:
        ordering = ['-pinned', 'pin_order', 'created_at']
        verbose_name = _('project')
        verbose_name_plural = _('projects')

    def __str__(self):
        return self.name


class Bucket(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE,
        related_name='buckets', verbose_name=_('project'),
    )
    name = models.CharField(_('name'), max_length=255)
    order = models.PositiveSmallIntegerField(_('order'), default=0)

    class Meta:
        ordering = ['order']
        verbose_name = _('bucket')
        verbose_name_plural = _('buckets')

    def __str__(self):
        return f'{self.project.name} / {self.name}'


class Task(models.Model):
    bucket = models.ForeignKey(
        Bucket, on_delete=models.CASCADE,
        related_name='tasks', verbose_name=_('bucket'),
    )
    title = models.CharField(_('title'), max_length=255)
    notes = models.TextField(_('notes'), blank=True)
    start_date = models.DateField(_('start date'), null=True, blank=True)
    end_date = models.DateField(_('end date'), null=True, blank=True)
    completed = models.BooleanField(_('completed'), default=False)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    position = models.PositiveIntegerField(_('position'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'created_at']
        verbose_name = _('task')
        verbose_name_plural = _('tasks')

    def __str__(self):
        return self.title


class ChecklistItem(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name='checklist_items', verbose_name=_('task'),
    )
    text = models.CharField(_('text'), max_length=500)
    checked = models.BooleanField(_('checked'), default=False)
    position = models.PositiveSmallIntegerField(_('position'), default=0)

    class Meta:
        ordering = ['position']
        verbose_name = _('checklist item')
        verbose_name_plural = _('checklist items')

    def __str__(self):
        return self.text


class Tag(models.Model):
    class Color(models.TextChoices):
        GOLD = 'gold', _('Gold')
        SILVER = 'silver', _('Silver')
        COPPER = 'copper', _('Copper')
        BRASS = 'brass', _('Brass')
        BRONZE = 'bronze', _('Bronze')
        GUNMETAL = 'gunmetal', _('Gunmetal')
        ROSE_GOLD = 'rose_gold', _('Rose Gold')
        PEWTER = 'pewter', _('Pewter')

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE,
        related_name='tags', verbose_name=_('project'),
    )
    name = models.CharField(_('name'), max_length=100)
    color = models.CharField(_('color'), max_length=20, choices=Color.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'color'],
                name='unique_tag_color_per_project',
            )
        ]
        verbose_name = _('tag')
        verbose_name_plural = _('tags')

    def __str__(self):
        return f'{self.name} ({self.color})'


class TaskTag(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name='task_tags', verbose_name=_('task'),
    )
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE,
        related_name='task_tags', verbose_name=_('tag'),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['task', 'tag'],
                name='unique_task_tag',
            )
        ]
        verbose_name = _('task tag')
        verbose_name_plural = _('task tags')

    def __str__(self):
        return f'{self.task.title} — {self.tag.name}'

from django.contrib import admin

from .models import Bucket, ChecklistItem, Project, Tag, Task, TaskTag


class BucketInline(admin.TabularInline):
    model = Bucket
    extra = 0


class TagInline(admin.TabularInline):
    model = Tag
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'pinned', 'pin_order', 'created_at']
    list_filter = ['pinned', 'owner']
    search_fields = ['name']
    inlines = [BucketInline, TagInline]


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0


class TaskTagInline(admin.TabularInline):
    model = TaskTag
    extra = 0


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'bucket', 'completed', 'start_date', 'end_date', 'position']
    list_filter = ['completed', 'bucket__project']
    search_fields = ['title']
    inlines = [ChecklistItemInline, TaskTagInline]


@admin.register(Bucket)
class BucketAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'order']
    list_filter = ['project']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'project']
    list_filter = ['color', 'project']

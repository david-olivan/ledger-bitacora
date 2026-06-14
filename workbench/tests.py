from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import Bucket, Project, Tag, Task, TaskTag

User = get_user_model()


class WorkbenchTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='owner', password='pw')
        self.client.force_login(self.user)

    def _make_project(self, name='Proj'):
        project = Project.objects.create(name=name, owner=self.user)
        bucket = Bucket.objects.create(project=project, name='In Progress', order=0)
        return project, bucket


class ProjectRulesTests(WorkbenchTestCase):
    def test_project_create_seeds_default_bucket(self):
        self.client.post(reverse('workbench:project_create'), {'name': 'New'})
        project = Project.objects.get(name='New')
        self.assertEqual(project.buckets.count(), 1)

    def test_pin_limit_is_five(self):
        projects = [Project.objects.create(name=f'P{i}', owner=self.user) for i in range(6)]
        for project in projects:
            self.client.post(reverse('workbench:project_pin', args=[project.pk]))
        self.assertEqual(Project.objects.filter(owner=self.user, pinned=True).count(), 5)

    def test_pinned_projects_in_context(self):
        project, _ = self._make_project()
        self.client.post(reverse('workbench:project_pin', args=[project.pk]))
        response = self.client.get(reverse('workbench:project_list'))
        self.assertIn(project, response.context['pinned_projects'])


class BucketRulesTests(WorkbenchTestCase):
    def test_bucket_create_caps_at_seven(self):
        project, _ = self._make_project()
        for i in range(10):
            self.client.post(reverse('workbench:bucket_create', args=[project.pk]), {'name': f'B{i}'})
        self.assertEqual(project.buckets.count(), 7)

    def test_bucket_rename(self):
        project, bucket = self._make_project()
        self.client.post(reverse('workbench:bucket_rename', args=[bucket.pk]), {'name': 'Renamed'})
        bucket.refresh_from_db()
        self.assertEqual(bucket.name, 'Renamed')

    def test_bucket_delete(self):
        project, bucket = self._make_project()
        self.client.post(reverse('workbench:bucket_delete', args=[bucket.pk]))
        self.assertFalse(Bucket.objects.filter(pk=bucket.pk).exists())


class TaskRulesTests(WorkbenchTestCase):
    def test_complete_toggles_completed_at(self):
        project, bucket = self._make_project()
        task = Task.objects.create(bucket=bucket, title='T')
        self.client.post(reverse('workbench:task_complete', args=[task.pk]))
        task.refresh_from_db()
        self.assertTrue(task.completed)
        self.assertIsNotNone(task.completed_at)
        self.client.post(reverse('workbench:task_complete', args=[task.pk]))
        task.refresh_from_db()
        self.assertFalse(task.completed)
        self.assertIsNone(task.completed_at)

    def test_task_update_caps_tags_at_three(self):
        project, bucket = self._make_project()
        task = Task.objects.create(bucket=bucket, title='T')
        colors = ['gold', 'silver', 'copper', 'brass']
        tags = [Tag.objects.create(project=project, name=c, color=c) for c in colors]
        self.client.post(
            reverse('workbench:task_update', args=[task.pk]),
            {'title': 'T', 'tags': [t.pk for t in tags]},
        )
        self.assertEqual(task.task_tags.count(), 3)

    def test_reorder_moves_task_between_buckets(self):
        project, bucket_a = self._make_project()
        bucket_b = Bucket.objects.create(project=project, name='Done', order=1)
        task = Task.objects.create(bucket=bucket_a, title='T', position=0)
        self.client.post(reverse('workbench:task_reorder'), {
            'task_id': task.pk, 'bucket_id': bucket_b.pk, 'position': 0,
        })
        task.refresh_from_db()
        self.assertEqual(task.bucket_id, bucket_b.pk)


class TagRulesTests(WorkbenchTestCase):
    def test_one_tag_per_color_per_project(self):
        project, _ = self._make_project()
        Tag.objects.create(project=project, name='Gold A', color='gold')
        with self.assertRaises(IntegrityError):
            Tag.objects.create(project=project, name='Gold B', color='gold')

    def test_tag_rename_propagates(self):
        project, bucket = self._make_project()
        tag = Tag.objects.create(project=project, name='Old', color='gold')
        task = Task.objects.create(bucket=bucket, title='T')
        TaskTag.objects.create(task=task, tag=tag)
        self.client.post(reverse('workbench:tag_update', args=[tag.pk]), {'name': 'New'})
        self.assertEqual(task.task_tags.first().tag.name, 'New')


class AccessControlTests(WorkbenchTestCase):
    def test_login_required(self):
        self.client.logout()
        response = self.client.get(reverse('workbench:project_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_cannot_access_other_users_project(self):
        other = User.objects.create_user(username='intruder', password='pw')
        project = Project.objects.create(name='Secret', owner=other)
        response = self.client.get(reverse('workbench:project_detail', args=[project.pk]))
        self.assertEqual(response.status_code, 404)

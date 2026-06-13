from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('pinned', models.BooleanField(default=False, verbose_name='pinned')),
                ('pin_order', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='pin order')),
                ('owner', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='projects',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='owner',
                )),
            ],
            options={
                'verbose_name': 'project',
                'verbose_name_plural': 'projects',
                'ordering': ['-pinned', 'pin_order', 'created_at'],
            },
        ),
        migrations.CreateModel(
            name='Bucket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='order')),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='buckets',
                    to='workbench.project',
                    verbose_name='project',
                )),
            ],
            options={
                'verbose_name': 'bucket',
                'verbose_name_plural': 'buckets',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('notes', models.TextField(blank=True, verbose_name='notes')),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='start date')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='end date')),
                ('completed', models.BooleanField(default=False, verbose_name='completed')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='completed at')),
                ('position', models.PositiveIntegerField(default=0, verbose_name='position')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('bucket', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tasks',
                    to='workbench.bucket',
                    verbose_name='bucket',
                )),
            ],
            options={
                'verbose_name': 'task',
                'verbose_name_plural': 'tasks',
                'ordering': ['position', 'created_at'],
            },
        ),
        migrations.CreateModel(
            name='ChecklistItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=500, verbose_name='text')),
                ('checked', models.BooleanField(default=False, verbose_name='checked')),
                ('position', models.PositiveSmallIntegerField(default=0, verbose_name='position')),
                ('task', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='checklist_items',
                    to='workbench.task',
                    verbose_name='task',
                )),
            ],
            options={
                'verbose_name': 'checklist item',
                'verbose_name_plural': 'checklist items',
                'ordering': ['position'],
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('color', models.CharField(
                    choices=[
                        ('gold', 'Gold'),
                        ('silver', 'Silver'),
                        ('copper', 'Copper'),
                        ('brass', 'Brass'),
                        ('bronze', 'Bronze'),
                        ('gunmetal', 'Gunmetal'),
                        ('rose_gold', 'Rose Gold'),
                        ('pewter', 'Pewter'),
                    ],
                    max_length=20,
                    verbose_name='color',
                )),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tags',
                    to='workbench.project',
                    verbose_name='project',
                )),
            ],
            options={
                'verbose_name': 'tag',
                'verbose_name_plural': 'tags',
            },
        ),
        migrations.AddConstraint(
            model_name='tag',
            constraint=models.UniqueConstraint(
                fields=['project', 'color'],
                name='unique_tag_color_per_project',
            ),
        ),
        migrations.CreateModel(
            name='TaskTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='task_tags',
                    to='workbench.task',
                    verbose_name='task',
                )),
                ('tag', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='task_tags',
                    to='workbench.tag',
                    verbose_name='tag',
                )),
            ],
            options={
                'verbose_name': 'task tag',
                'verbose_name_plural': 'task tags',
            },
        ),
        migrations.AddConstraint(
            model_name='tasktag',
            constraint=models.UniqueConstraint(
                fields=['task', 'tag'],
                name='unique_task_tag',
            ),
        ),
    ]

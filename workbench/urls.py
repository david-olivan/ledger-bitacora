from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'workbench'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('project/new/', views.project_create, name='project_create'),
    path('project/<int:pk>/', views.project_detail, name='project_detail'),
    path('project/<int:pk>/pin/', views.project_pin, name='project_pin'),
    path('project/<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('bucket/<int:bucket_pk>/task/new/', views.task_create, name='task_create'),
    path('task/<int:pk>/', views.task_detail, name='task_detail'),
    path('task/<int:pk>/update/', views.task_update, name='task_update'),
    path('task/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('task/<int:pk>/complete/', views.task_complete, name='task_complete'),
    path('task/<int:task_pk>/checklist/add/', views.checklist_item_add, name='checklist_item_add'),
    path('checklist/<int:pk>/toggle/', views.checklist_item_toggle, name='checklist_item_toggle'),
    path('checklist/<int:pk>/delete/', views.checklist_item_delete, name='checklist_item_delete'),
]

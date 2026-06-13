from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Project


@login_required
def project_list(request):
    projects = Project.objects.filter(owner=request.user)
    return render(request, 'workbench/project_list.html', {'projects': projects})

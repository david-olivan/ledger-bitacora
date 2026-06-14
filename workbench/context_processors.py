from .models import Project


def pinned_projects(request):
    if not request.user.is_authenticated:
        return {}
    projects = Project.objects.filter(owner=request.user, pinned=True).order_by('pin_order')
    return {'pinned_projects': projects}

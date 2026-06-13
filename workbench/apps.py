from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WorkbenchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workbench'
    verbose_name = _('Workbench')

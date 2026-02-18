from django.apps import AppConfig


class AlumniappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alumniapp'

from django.apps import AppConfig

class YourAppConfig(AppConfig):
    name = 'alumniapp'

    def ready(self):
        import alumniapp.signals


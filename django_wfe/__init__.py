from django.apps import AppConfig
from .utils import order_workflow_execution


class DjangoWfeConfig(AppConfig):
    name = 'django_wfe'
    verbose_name = 'Django Workflow Engine'

    def ready(self):
        self.set_default_settings()
        self.set_watchdog_on_wdk_models()

    def set_default_settings(self):
        """
        Method complementing project settings with default Django WFE settings.

        :return: None
        """
        from . import settings as defaults
        from django.conf import settings
        for name in dir(defaults):
            if name.isupper() and not hasattr(settings, name):
                setattr(settings, name, getattr(defaults, name))

    def set_watchdog_on_wdk_models(self):
        """
        Method starting a background thread updating database with user defined Steps, Decisions and Workflows.

        :return: None
        """
        import atexit
        from apscheduler.schedulers.background import BackgroundScheduler

        from .models import Watchdog
        from .utils import update_wdk_models, deregister_watchdog

        watchdog = Watchdog.load()

        if not watchdog.running:
            # order deregister_watchdog() executions as exit function.
            atexit.register(deregister_watchdog)

            # mark watchdog as running
            watchdog.running = True
            watchdog.save()
            # schedule periodic watchdog's execution
            scheduler = BackgroundScheduler(daemon=True)
            scheduler.add_job(update_wdk_models, 'interval', seconds=5)
            scheduler.start()


default_app_config = 'django_wfe.DjangoWfeConfig'

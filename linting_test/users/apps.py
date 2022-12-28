from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "linting_test.users"
    verbose_name = _("Users")

    @staticmethod
    def ready():
        try:
            import linting_test.users.signals  # noqa F401
        except ImportError:
            pass

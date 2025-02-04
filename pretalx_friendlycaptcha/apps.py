from django.apps import AppConfig
from django.utils.translation import gettext_lazy

from . import __version__


class PluginApp(AppConfig):
    name = "pretalx_friendlycaptcha"
    verbose_name = "FriendlyCaptcha CfP step"

    class PretalxPluginMeta:
        name = gettext_lazy("FriendlyCaptcha CfP step")
        author = "Tobias Kunze"
        description = gettext_lazy(
            "Adds a new, final CfP step with the FriendlyCaptcha captcha, in order to reduce spam. You need a FriendlyCaptcha account/subscription to use this plugin."
        )
        visible = True
        version = __version__
        category = "INTEGRATION"

    def ready(self):
        from . import signals  # NOQA

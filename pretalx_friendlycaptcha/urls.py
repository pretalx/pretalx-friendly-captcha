from django.urls import re_path
from pretalx.event.models.event import SLUG_REGEX

from .views import FriendlycaptchaSettingsView

urlpatterns = [
    re_path(
        rf"^orga/event/(?P<event>{SLUG_REGEX})/settings/p/pretalx_friendlycaptcha/$",
        FriendlycaptchaSettingsView.as_view(),
        name="settings",
    ),
]

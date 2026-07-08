import pytest
from django_scopes import scopes_disabled

from pretalx.event.domain.event import shred_event

from pretalx_friendlycaptcha.models import FriendlycaptchaSettings


@pytest.mark.django_db
def test_shred_event_with_friendlycaptcha_settings(event):
    with scopes_disabled():
        FriendlycaptchaSettings.objects.create(event=event, secret="x", site_key="y")
        assert FriendlycaptchaSettings.objects.count() == 1
        shred_event(event)
        assert FriendlycaptchaSettings.objects.count() == 0

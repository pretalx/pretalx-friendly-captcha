from django.dispatch import receiver
from django.urls import reverse

from pretalx.cfp.signals import cfp_steps
from pretalx.orga.signals import event_copy_data, nav_event_settings

from .models import FriendlycaptchaSettings


@receiver(nav_event_settings)
def pretalx_friendlycaptcha_settings(sender, request, **kwargs):
    if not request.user.has_perm("event.update_event", request.event):
        return []
    return [
        {
            "label": "FriendlyCaptcha",
            "url": reverse(
                "plugins:pretalx_friendlycaptcha:settings",
                kwargs={"event": request.event.slug},
            ),
            "active": request.resolver_match.url_name
            == "plugins:pretalx_friendlycaptcha:settings",
        }
    ]


@receiver(cfp_steps)
def pretalx_friendlycaptcha_cfp_steps(sender, **kwargs):
    from pretalx_friendlycaptcha.forms import FriendlyCaptchaCfpStep  # noqa: PLC0415

    return [FriendlyCaptchaCfpStep]


@receiver(event_copy_data, dispatch_uid="friendlycaptcha_copy_data")
def copy_event_settings(sender, other, **kwargs):
    old_settings = FriendlycaptchaSettings.objects.filter(
        event__slug__iexact=other
    ).first()
    if not old_settings:
        return
    old_settings.pk = None
    old_settings.event = sender
    old_settings.save()

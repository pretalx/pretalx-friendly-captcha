from django.dispatch import receiver
from django.urls import reverse
from pretalx.cfp.signals import cfp_steps
from pretalx.orga.signals import nav_event_settings


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
    from pretalx_friendlycaptcha.forms import FriendlyCaptchaCfpStep

    return [FriendlyCaptchaCfpStep]

from django.db import models


class FriendlycaptchaSettings(models.Model):
    event = models.OneToOneField(
        to="event.Event",
        on_delete=models.CASCADE,
        related_name="pretalx_friendlycaptcha_settings",
    )
    site_key = models.CharField(max_length=200, default="")

from django.db import models


class FriendlycaptchaSettings(models.Model):
    event = models.OneToOneField(
        to="event.Event",
        on_delete=models.CASCADE,
        related_name="pretalx_friendlycaptcha_settings",
    )
    secret = models.CharField(max_length=200, default="")
    site_key = models.CharField(max_length=200, default="", null=True, blank=True)
    endpoint = models.CharField(
        max_length=200,
        choices=[("US", "US"), ("EU", "EU")],
        default="US",
        help_text="If you are on the Advanced or Enterprise plan, you can set the location of the endpoint to EU.",
    )

    @property
    def base_url(self):
        if self.endpoint == "US":
            return "https://api.friendlycaptcha.com/api/v1/"
        return "https://eu-api.friendlycaptcha.eu/api/v1/"

    @property
    def puzzle_url(self):
        return self.base_url + "puzzle"

    @property
    def verify_url(self):
        return self.base_url + "siteverify"

import requests
from django import forms
from django.utils.translation import gettext_lazy as _
from i18nfield.forms import I18nModelForm
from pretalx.cfp.flow import FormFlowStep, GenericFlowStep

from .models import FriendlycaptchaSettings


class FriendlycaptchaSettingsForm(I18nModelForm):

    def __init__(self, *args, event=None, **kwargs):
        self.instance, _ = FriendlycaptchaSettings.objects.get_or_create(event=event)
        super().__init__(*args, **kwargs, instance=self.instance, locales=event.locales)

    class Meta:
        model = FriendlycaptchaSettings
        fields = ("site_key",)
        widgets = {}


class FriendlyCaptchaCfpForm(forms.Form):
    frc_captcha_solution = forms.CharField()

    def clean_frc_captcha_solution(self):
        key = self.cleaned_data["frc_captcha_solution"]
        if not key:
            raise forms.ValidationError("Please solve the captcha.")
        request_data = {
            "solution": key,
            "secret": self.event.pretalx_friendlycaptcha_settings.secret,
        }
        if self.event.pretalx_friendlycaptcha_settings.site_key:
            request_data["sitekey"] = (
                self.event.pretalx_friendlycaptcha_settings.site_key
            )
        try:
            response = requests.post(
                self.event.pretalx_friendlycaptcha_settings.verify_url,
                json=request_data,
                timeout=10,
            )
            response.raise_for_status()
            # We don't look at the response content, as the docs state that in
            # production, any 200 response is a success.
        except Exception as e:
            raise forms.ValidationError("Could not verify captcha: {}".format(e))
        return "valid"


class FriendlyCaptchaCfpStep(FormFlowStep, GenericFlowStep):
    identifier = "friendlycaptcha"
    icon = "puzzle-piece"
    form_class = FriendlyCaptchaCfpForm
    priority = 1000
    template_name = "pretalx_friendlycaptcha/submission_captcha.html"

    @property
    def label(self):
        return _("Captcha")

    @property
    def _title(self):
        return _("One last thing …")

    @property
    def _text(self):
        return ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["captcha_site_key"] = self.event.pretalx_friendlycaptcha_settings.site_key
        return ctx

    def get_form_kwargs(self):
        return {}

    def get_form(self, **kwargs):
        if self.request.method == "POST":
            return self.form_class(
                data={
                    "frc_captcha_solution": self.request.POST.get(
                        "frc-captcha-solution"
                    )
                },
                **self.get_form_kwargs(),
            )
        return super().get_form(**kwargs)

    def get_csp_update(self, request):
        return {
            "script-src": "'unsafe-eval'",
            "worker-src": "'self' 'unsafe-eval' blob:",
            "connect-src": f"'self' {request.event.pretalx_friendlycaptcha_settings.puzzle_url}",
        }

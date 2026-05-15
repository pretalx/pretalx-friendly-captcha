import urllib3
from django import forms
from django.utils.translation import gettext_lazy as _
from i18nfield.forms import I18nModelForm

from pretalx.cfp.flow import FormFlowStep

from .models import FriendlycaptchaSettings


class FriendlycaptchaSettingsForm(I18nModelForm):
    def __init__(self, *args, event=None, **kwargs):
        self.instance, _ = FriendlycaptchaSettings.objects.get_or_create(event=event)
        super().__init__(*args, **kwargs, instance=self.instance, locales=event.locales)

    class Meta:
        model = FriendlycaptchaSettings
        fields = ("secret", "site_key", "endpoint")
        widgets = {}


class FriendlyCaptchaCfpForm(forms.Form):
    frc_captcha_solution = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, event=None, from_storage=False, **kwargs):
        self.event = event
        self.from_storage = from_storage
        kwargs.pop("field_configuration", None)
        super().__init__(*args, **kwargs)

    def clean_frc_captcha_solution(self):
        key = self.cleaned_data["frc_captcha_solution"]
        if not key:
            raise forms.ValidationError("Please solve the captcha.")
        if self.from_storage and key == "valid":
            return "valid"
        request_data = {
            "solution": key,
            "secret": self.event.pretalx_friendlycaptcha_settings.secret,
        }
        if self.event.pretalx_friendlycaptcha_settings.site_key:
            request_data["sitekey"] = (
                self.event.pretalx_friendlycaptcha_settings.site_key
            )
        try:
            response = urllib3.request(
                "POST",
                self.event.pretalx_friendlycaptcha_settings.verify_url,
                json=request_data,
                timeout=10,
            )
            if response.status >= 400:
                raise forms.ValidationError(
                    f"Could not verify captcha: HTTP {response.status}"
                )
            response_data = response.json()
        except (urllib3.exceptions.HTTPError, OSError, ValueError) as e:
            raise forms.ValidationError(f"Could not verify captcha: {e}") from e
        if not response_data.get("success"):
            raise forms.ValidationError("Captcha verification failed.")
        return "valid"


class FriendlyCaptchaCfpStep(FormFlowStep):
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
        return {"event": self.request.event}

    def get_form(self, from_storage=False):
        # A fresh POST carries the single-use solution token from the widget
        # under a dashed field name; validate it against the API. All other
        # cases (GET render, and the cached re-check on submit) reload the
        # already-verified "valid" marker from session storage, so the
        # single-use token is never sent to the API twice.
        if self.request.method == "POST" and not from_storage:
            return self.form_class(
                data={
                    "frc_captcha_solution": self.request.POST.get(
                        "frc-captcha-solution"
                    )
                },
                **self.get_form_kwargs(),
            )
        return self.form_class(
            data=self.get_form_data() or None,
            from_storage=from_storage,
            **self.get_form_kwargs(),
        )

    def get_csp_update(self, request):
        return {
            "script-src": "'unsafe-eval'",
            "worker-src": "'self' 'unsafe-eval' blob:",
            "connect-src": f"'self' {request.event.pretalx_friendlycaptcha_settings.puzzle_url}",
        }

import types
from unittest.mock import MagicMock, patch

import pytest
import urllib3
from django.urls import reverse

from pretalx_friendlycaptcha.forms import FriendlyCaptchaCfpForm, FriendlyCaptchaCfpStep
from pretalx_friendlycaptcha.models import FriendlycaptchaSettings
from pretalx_friendlycaptcha.signals import pretalx_friendlycaptcha_cfp_steps

SETTINGS_URL_NAME = "plugins:pretalx_friendlycaptcha:settings"


@pytest.mark.django_db
def test_orga_can_access_settings(orga_client, event):
    response = orga_client.get(
        reverse(SETTINGS_URL_NAME, kwargs={"event": event.slug}), follow=True
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_orga_can_save_settings(orga_client, event):
    url = reverse(SETTINGS_URL_NAME, kwargs={"event": event.slug})
    response = orga_client.post(
        url,
        {"secret": "testsecret", "site_key": "FC123", "endpoint": "EU"},
        follow=True,
    )
    assert response.status_code == 200
    settings = FriendlycaptchaSettings.objects.get(event=event)
    assert settings.secret == "testsecret"
    assert settings.site_key == "FC123"
    assert settings.endpoint == "EU"


@pytest.mark.django_db
def test_reviewer_cannot_access_settings(review_client, event):
    response = review_client.get(
        reverse(SETTINGS_URL_NAME, kwargs={"event": event.slug})
    )
    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("endpoint", "expected_base"),
    (
        ("US", "https://api.friendlycaptcha.com/api/v1/"),
        ("EU", "https://eu-api.friendlycaptcha.eu/api/v1/"),
    ),
)
def test_settings_urls(event, endpoint, expected_base):
    settings = FriendlycaptchaSettings.objects.create(
        event=event, secret="s", site_key="k", endpoint=endpoint
    )
    assert settings.base_url == expected_base
    assert settings.puzzle_url == expected_base + "puzzle"
    assert settings.verify_url == expected_base + "siteverify"


@pytest.mark.django_db
def test_captcha_form_rejects_empty_solution(event):
    FriendlycaptchaSettings.objects.create(event=event, secret="s", site_key="k")
    form = FriendlyCaptchaCfpForm(data={"frc_captcha_solution": ""}, event=event)
    assert not form.is_valid()
    assert "frc_captcha_solution" in form.errors


@pytest.mark.django_db
def test_captcha_form_accepts_valid_from_storage(event):
    FriendlycaptchaSettings.objects.create(event=event, secret="s", site_key="k")
    form = FriendlyCaptchaCfpForm(
        data={"frc_captcha_solution": "valid"}, event=event, from_storage=True
    )
    assert form.is_valid()


@pytest.mark.django_db
def test_captcha_form_verifies_with_api(event):
    FriendlycaptchaSettings.objects.create(event=event, secret="s", site_key="k")
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json.return_value = {"success": True}
    with patch(
        "pretalx_friendlycaptcha.forms.urllib3.request", return_value=mock_response
    ) as mock_post:
        form = FriendlyCaptchaCfpForm(
            data={"frc_captcha_solution": "solution123"}, event=event
        )
        assert form.is_valid()
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["json"]["solution"] == "solution123"
        assert call_kwargs.kwargs["json"]["secret"] == "s"
        assert call_kwargs.kwargs["json"]["sitekey"] == "k"


@pytest.mark.django_db
def test_captcha_form_rejects_failed_verification(event):
    FriendlycaptchaSettings.objects.create(event=event, secret="s", site_key="k")
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json.return_value = {"success": False}
    with patch(
        "pretalx_friendlycaptcha.forms.urllib3.request", return_value=mock_response
    ):
        form = FriendlyCaptchaCfpForm(
            data={"frc_captcha_solution": "badsolution"}, event=event
        )
        assert not form.is_valid()


@pytest.mark.django_db
def test_captcha_form_handles_api_error(event):
    FriendlycaptchaSettings.objects.create(event=event, secret="s", site_key="k")
    with patch(
        "pretalx_friendlycaptcha.forms.urllib3.request",
        side_effect=urllib3.exceptions.HTTPError("timeout"),
    ):
        form = FriendlyCaptchaCfpForm(
            data={"frc_captcha_solution": "solution123"}, event=event
        )
        assert not form.is_valid()
        assert "Could not verify captcha" in str(form.errors["frc_captcha_solution"])


@pytest.mark.django_db
def test_captcha_form_rejects_http_error_status(event):
    FriendlycaptchaSettings.objects.create(event=event, secret="s", site_key="k")
    mock_response = MagicMock()
    mock_response.status = 503
    with patch(
        "pretalx_friendlycaptcha.forms.urllib3.request", return_value=mock_response
    ):
        form = FriendlyCaptchaCfpForm(
            data={"frc_captcha_solution": "solution123"}, event=event
        )
        assert not form.is_valid()
        assert "HTTP 503" in str(form.errors["frc_captcha_solution"])


def test_cfp_steps_signal_returns_step():
    assert pretalx_friendlycaptcha_cfp_steps(None) == [FriendlyCaptchaCfpStep]


@pytest.mark.django_db
def test_cfp_step_labels(event):
    step = FriendlyCaptchaCfpStep(event=event)
    assert str(step.label) == "Captcha"
    assert str(step._title) == "One last thing …"
    assert step._text == ""


@pytest.mark.django_db
def test_cfp_step_context_data(event):
    FriendlycaptchaSettings.objects.create(event=event, secret="s", site_key="mykey")
    step = FriendlyCaptchaCfpStep(event=event)
    with patch(
        "pretalx_friendlycaptcha.forms.FormFlowStep.get_context_data", return_value={}
    ):
        ctx = step.get_context_data()
    assert ctx["captcha_site_key"] == "mykey"


@pytest.mark.django_db
def test_cfp_step_form_kwargs(event):
    step = FriendlyCaptchaCfpStep(event=event)
    step.request = types.SimpleNamespace(event=event)
    assert step.get_form_kwargs() == {"event": event}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("method", "from_storage"),
    (("POST", False), ("POST", True), ("GET", False), ("GET", True)),
)
def test_cfp_step_get_form(event, method, from_storage):
    FriendlycaptchaSettings.objects.create(event=event, secret="s", site_key="k")
    step = FriendlyCaptchaCfpStep(event=event)
    step.request = types.SimpleNamespace(
        event=event, method=method, POST={"frc-captcha-solution": "abc"}
    )
    step.get_form_data = lambda: {"frc_captcha_solution": "valid"}
    form = step.get_form(from_storage=from_storage)
    assert isinstance(form, FriendlyCaptchaCfpForm)
    # A fresh POST maps the dashed widget field; storage paths carry the
    # from_storage flag so the cached "valid" token short-circuits.
    if method == "POST" and not from_storage:
        assert form.data["frc_captcha_solution"] == "abc"
        assert form.from_storage is False
    else:
        assert form.from_storage is from_storage


@pytest.mark.django_db
def test_cfp_step_is_completed_uses_cached_token(event):
    # Regression: the step must inherit a working is_completed() from
    # FormFlowStep. When the captcha was solved earlier, the cached "valid"
    # marker is reloaded from storage and accepted without re-hitting the
    # single-use-token API.
    FriendlycaptchaSettings.objects.create(event=event, secret="s", site_key="k")
    step = FriendlyCaptchaCfpStep(event=event)
    request = types.SimpleNamespace(event=event, method="POST", POST={})
    with patch("pretalx_friendlycaptcha.forms.urllib3.request") as mock_post:
        step.get_form_data = lambda: {"frc_captcha_solution": "valid"}
        assert step.is_completed(request) is True
        step.get_form_data = dict
        assert step.is_completed(request) is False
        mock_post.assert_not_called()


@pytest.mark.django_db
def test_cfp_step_csp_update(event):
    FriendlycaptchaSettings.objects.create(event=event, secret="s", site_key="k")
    step = FriendlyCaptchaCfpStep(event=event)
    request = types.SimpleNamespace(event=event)
    csp = step.get_csp_update(request)
    assert event.pretalx_friendlycaptcha_settings.puzzle_url in csp["connect-src"]


@pytest.mark.django_db
def test_captcha_form_omits_sitekey_when_blank(event):
    FriendlycaptchaSettings.objects.create(event=event, secret="s", site_key="")
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json.return_value = {"success": True}
    with patch(
        "pretalx_friendlycaptcha.forms.urllib3.request", return_value=mock_response
    ) as mock_post:
        form = FriendlyCaptchaCfpForm(
            data={"frc_captcha_solution": "solution123"}, event=event
        )
        assert form.is_valid()
        assert "sitekey" not in mock_post.call_args.kwargs["json"]

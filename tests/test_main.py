from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from pretalx_friendlycaptcha.forms import FriendlyCaptchaCfpForm
from pretalx_friendlycaptcha.models import FriendlycaptchaSettings

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
    mock_response.json.return_value = {"success": True}
    mock_response.raise_for_status = MagicMock()
    with patch(
        "pretalx_friendlycaptcha.forms.requests.post", return_value=mock_response
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
    mock_response.json.return_value = {"success": False}
    mock_response.raise_for_status = MagicMock()
    with patch(
        "pretalx_friendlycaptcha.forms.requests.post", return_value=mock_response
    ):
        form = FriendlyCaptchaCfpForm(
            data={"frc_captcha_solution": "badsolution"}, event=event
        )
        assert not form.is_valid()


@pytest.mark.django_db
def test_captcha_form_handles_api_error(event):
    FriendlycaptchaSettings.objects.create(event=event, secret="s", site_key="k")
    with patch(
        "pretalx_friendlycaptcha.forms.requests.post", side_effect=Exception("timeout")
    ):
        form = FriendlyCaptchaCfpForm(
            data={"frc_captcha_solution": "solution123"}, event=event
        )
        assert not form.is_valid()
        assert "Could not verify captcha" in str(form.errors["frc_captcha_solution"])


@pytest.mark.django_db
def test_captcha_form_omits_sitekey_when_blank(event):
    FriendlycaptchaSettings.objects.create(event=event, secret="s", site_key="")
    mock_response = MagicMock()
    mock_response.json.return_value = {"success": True}
    mock_response.raise_for_status = MagicMock()
    with patch(
        "pretalx_friendlycaptcha.forms.requests.post", return_value=mock_response
    ) as mock_post:
        form = FriendlyCaptchaCfpForm(
            data={"frc_captcha_solution": "solution123"}, event=event
        )
        assert form.is_valid()
        assert "sitekey" not in mock_post.call_args.kwargs["json"]

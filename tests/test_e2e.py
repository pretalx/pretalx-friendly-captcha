from unittest.mock import MagicMock, patch

import pytest
from django_scopes import scope, scopes_disabled

from pretalx.person.models import User
from pretalx.submission.models import Submission, SubmissionStates

from pretalx_friendlycaptcha.models import FriendlycaptchaSettings


def _follow(client, url, method="POST", data=None):
    if method == "GET":
        response = client.get(url, follow=True, data=data)
    else:
        response = client.post(url, follow=True, data=data)
    try:
        final_url = response.redirect_chain[-1][0]
    except IndexError:
        final_url = url
    return response, final_url


@pytest.fixture
def submitter():
    with scopes_disabled():
        return User.objects.create_user(
            email="speaker@example.org", password="speakerpassw0rd", name="Sam Speaker"
        )


@pytest.mark.django_db
def test_e2e_cfp_submission_through_captcha_step(event, submitter, client):
    # Full CfP wizard: info -> profile -> friendlycaptcha -> submitted.
    # Regression guard for the broken base class: before the FormFlowStep
    # fix, POSTing the captcha step raised NotImplementedError / 405 and a
    # proposal could never be submitted while the plugin was enabled.
    FriendlycaptchaSettings.objects.create(event=event, secret="s", site_key="k")
    client.force_login(submitter)

    _, info_url = _follow(client, f"/{event.slug}/submit/", method="GET")
    assert "/info/" in info_url

    with scopes_disabled():
        sub_type = event.cfp.default_type_id

    info = {
        "title": "My captcha-protected talk",
        "content_locale": "en",
        "description": "Description",
        "abstract": "Abstract",
        "notes": "Notes",
        "slot_count": 1,
        "submission_type": sub_type,
        "additional_speaker": "",
        "resource-TOTAL_FORMS": "0",
        "resource-INITIAL_FORMS": "0",
        "resource-MIN_NUM_FORMS": "0",
        "resource-MAX_NUM_FORMS": "1000",
    }
    _, profile_url = _follow(client, info_url, data=info)
    assert "/profile/" in profile_url

    _, captcha_url = _follow(
        client, profile_url, data={"name": "Sam Speaker", "biography": "Hi"}
    )
    assert "/friendlycaptcha/" in captcha_url

    # The captcha step renders the widget with the configured site key.
    response = client.get(captcha_url)
    assert response.status_code == 200
    assert 'data-sitekey="k"' in response.content.decode()

    # Solving the captcha submits the single-use token under the dashed
    # field name; the verification API is mocked to succeed.
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json.return_value = {"success": True}
    with patch(
        "pretalx_friendlycaptcha.forms.urllib3.request", return_value=mock_response
    ) as mock_verify:
        _, final_url = _follow(
            client, captcha_url, data={"frc-captcha-solution": "the-token"}
        )

    assert "/me/submissions/" in final_url
    # The single-use token is verified exactly once: the final is_completed()
    # re-check reuses the cached "valid" marker instead of re-hitting the API.
    mock_verify.assert_called_once()
    assert mock_verify.call_args.kwargs["json"]["solution"] == "the-token"

    with scope(event=event):
        sub = Submission.objects.get(title="My captcha-protected talk")
        assert sub.state == SubmissionStates.SUBMITTED
        assert sub.speakers.filter(user=submitter).exists()

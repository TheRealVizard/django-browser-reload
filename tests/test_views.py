from http import HTTPStatus
from pathlib import Path

import django
import pytest
from django.conf import settings
from django.test import SimpleTestCase

from django_browser_reload.views import current_version, template_changed_event

if django.VERSION >= (3, 2):
    from django_browser_reload.views import template_changed

django_3_2_plus = pytest.mark.skipif(
    django.VERSION < (3, 2), reason="Requires Django 3.2+"
)


@django_3_2_plus
class TemplateChangedTests(SimpleTestCase):
    def test_ignored(self):
        template_changed(file_path=Path("/tmp/nothing"))

        assert not template_changed_event.is_set()

    def test_success(self):
        path = settings.BASE_DIR / "templates" / "example.html"

        template_changed(file_path=path)

        assert template_changed_event.is_set()
        template_changed_event.clear()


class EventsTests(SimpleTestCase):
    def test_success_version_id(self):
        response = self.client.get("/__reload__/events/")

        assert response.status_code == HTTPStatus.OK
        assert response["Content-Type"] == "text/event-stream"
        event = next(response.streaming_content)
        assert event == (
            b'data: {"type": "version", "version": "'
            + current_version.encode()
            + b'"}\n\n'
        )

    def test_success_template_change(self):
        response = self.client.get("/__reload__/events/")
        template_changed_event.set()

        assert response.status_code == HTTPStatus.OK
        assert response["Content-Type"] == "text/event-stream"
        # Skip version ID message
        next(response.streaming_content)
        event = next(response.streaming_content)
        assert event == b'data: {"type": "templateChange"}\n\n'
        assert not template_changed_event.is_set()

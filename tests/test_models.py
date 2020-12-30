from datetime import datetime

from django_event_sourcing.globals import get_event_handler_register
from django_event_sourcing.models import (
    Event,
    EventTypeField,
)
from freezegun import freeze_time
import pytest

from .event_types import DummyEventType


class TestEventType:
    def test_fully_qualified_value(self):
        assert DummyEventType.TEST.fully_qualified_value == "dummy.test"


class TestEventTypeField:
    def test_from_db_value(self):
        assert EventTypeField().from_db_value("dummy.test") == DummyEventType.TEST

    @pytest.mark.parametrize(
        "input,expected",
        [
            ("dummy.test", DummyEventType.TEST),
            (DummyEventType.TEST, DummyEventType.TEST),
        ],
    )
    def test_to_python(self, input, expected):
        assert EventTypeField().to_python(input) == expected

    def test_get_prep_value(self):
        assert EventTypeField().get_prep_value(DummyEventType.TEST) == "dummy.test"


class TestEvent:
    @pytest.fixture
    def event(self, admin_user):
        with freeze_time("2020-01-01"):
            return Event.objects.create(
                type=DummyEventType.TEST, payload={}, created_by=admin_user
            )

    def test_can_be_constructed(self, event, admin_user):
        assert event.id
        assert event.type == DummyEventType.TEST
        assert event.payload == {}
        assert event.created_at == datetime(2020, 1, 1)
        assert event.created_by == admin_user

    def test_handle(self, event, mocker):
        register = get_event_handler_register()
        mock = mocker.Mock()

        register.register(event_type=DummyEventType.TEST)(mock)

        event.handle()
        mock.assert_called_once_with(event)

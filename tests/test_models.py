from datetime import datetime

from django_event_sourcing.models import (
    Event,
    EventHandlerRegister,
    EventTypeField,
    EventTypeRegister,
)
from freezegun import freeze_time
import pytest

from .event_types import DummyEventType


class TestEventType:
    def test_fully_qualified_value(self):
        assert DummyEventType.TEST.fully_qualified_value == "dummy.test"


class TestEventTypeRegister:
    def test_populates_event_types(self, settings):
        register = EventTypeRegister(settings.EVENT_TYPES)
        assert register["dummy.test"] == DummyEventType.TEST


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
    @freeze_time("2020-01-01")
    def test_can_be_constructed(self, admin_user):
        event = Event.objects.create(
            type=DummyEventType.TEST, payload={}, created_by=admin_user
        )

        assert event.id
        assert event.type == DummyEventType.TEST
        assert event.payload == {}
        assert event.created_at == datetime(2020, 1, 1)
        assert event.created_by == admin_user


class TestEventHandlerRegister:
    def test_handle(self, admin_user, mocker):
        register = EventHandlerRegister()
        mock = mocker.Mock()

        @register.register(event_type=DummyEventType.TEST)
        def handler(event):
            mock(event.payload["message"])

        event = Event.objects.create(
            type=DummyEventType.TEST, payload={"message": "test"}, created_by=admin_user
        )

        register.handle(event)
        mock.assert_called_once_with("test")

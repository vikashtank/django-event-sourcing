from datetime import datetime

from django_event_sourcing.globals import get_event_handler_register
from django_event_sourcing.models import (
    Event,
    EventHandlerLog,
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


@pytest.fixture
def event(admin_user):
    with freeze_time("2020-01-01"):
        return Event.objects.create(
            type=DummyEventType.TEST, data={}, created_by=admin_user
        )


class TestEvent:
    def test_can_be_constructed(self, event, admin_user):
        assert event.id
        assert event.type == DummyEventType.TEST
        assert event.data == {}
        assert event.created_at == datetime(2020, 1, 1)
        assert event.created_by == admin_user

    def test_handle(self, event, mocker):
        event_handlers = get_event_handler_register()
        mock = mocker.Mock()
        mock.__name__ = "my_function"

        event_handlers.register(event_type=DummyEventType.TEST)(mock)

        event.handle()
        mock.assert_called_once_with(event)


@freeze_time("2020-01-01")
class TestEventHandlerLog:
    def test_can_be_constructed(self, event):
        log = EventHandlerLog.objects.create(
            status=EventHandlerLog.Status.PROCESSING,
            name="get_information",
            event=event,
        )
        assert log.id
        assert log.status == EventHandlerLog.Status.PROCESSING
        assert log.name == "get_information"
        assert log.created_at == datetime(2020, 1, 1)
        assert log.event == event

    def test_create_from_function(self, event):
        def get_more_information():
            pass

        log = EventHandlerLog.objects.create_from_function(
            status=EventHandlerLog.Status.PROCESSING,
            function=get_more_information,
            event=event,
        )
        assert log.id
        assert log.status == EventHandlerLog.Status.PROCESSING
        assert log.name == "get_more_information"
        assert log.created_at == datetime(2020, 1, 1)
        assert log.event == event

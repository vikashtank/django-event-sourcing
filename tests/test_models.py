from datetime import datetime
import uuid

from django_event_sourcing.globals import get_event_handler_register
from django_event_sourcing.models import (
    Event,
    EventHandlerLog,
    EventType,
    EventTypeField,
)
from freezegun import freeze_time
import pytest

from .event_types import DummyEventType


class TestEventType:
    def test_fully_qualified_value(self):
        assert DummyEventType.TEST.fully_qualified_value == "dummy.test"

    def test_hashes_with_namespace(self):
        class DumberEventType(EventType):
            TEST = "test"

            def get_namespace(self):
                return "dumber"

        assert hash(DumberEventType.TEST) != hash(DummyEventType.TEST)


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
    @pytest.fixture
    def mock_event_handler_for_test(self, mocker):
        event_handlers = get_event_handler_register()

        mock = mocker.Mock()
        mock.__name__ = "my_function"

        event_handlers.register(event_type=DummyEventType.TEST)(mock)

        return mock

    def test_can_be_constructed(self, event, admin_user):
        assert event.id
        assert event.type == DummyEventType.TEST
        assert event.data == {}
        assert event.created_at == datetime(2020, 1, 1)
        assert event.created_by == admin_user

    def test_can_encode_uuid(self, event):
        uuid_value = uuid.uuid4()
        event.data = {"uuid": uuid_value}
        event.save()
        event.refresh_from_db()
        assert event.data["uuid"] == str(uuid_value)

    def test_can_encode_model(self, event, admin_user):
        event.data = {"event": event}
        event.save()
        event.refresh_from_db()
        assert event.data["event"] == str(event.pk)

    def test_handle(self, event, mock_event_handler_for_test):
        event.handle()
        mock_event_handler_for_test.assert_called_once_with(event)

    def test_create_and_handle(self, admin_user, mock_event_handler_for_test):
        event, _ = Event.objects.create_and_handle(
            type=DummyEventType.TEST, data={}, created_by=admin_user
        )
        mock_event_handler_for_test.assert_called_once_with(event)


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

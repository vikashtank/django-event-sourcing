from django_event_sourcing.models import Event, EventHandlerLog

from django_event_sourcing.registers import (
    EventHandlerRegister,
    EventTypeRegister,
)

from .event_types import DummyEventType


class TestEventTypeRegister:
    def test_populates_event_types(self, settings):
        register = EventTypeRegister(settings.EVENT_TYPES)
        assert register["dummy.test"] == DummyEventType.TEST


class TestEventHandlerRegister:
    def test_handle(self, admin_user, mocker):
        event_handlers = EventHandlerRegister()
        mock = mocker.Mock()

        @event_handlers.register(event_type=DummyEventType.TEST)
        def handler(event):
            mock(event.data["message"])

        event = Event.objects.create(
            type=DummyEventType.TEST, data={"message": "test"}, created_by=admin_user
        )

        event_handlers.handle(event)
        mock.assert_called_once_with("test")

        log = event.handler_logs.get()
        assert log.status == EventHandlerLog.Status.SUCCESS

    def test_handles_failure(self, admin_user, mocker):
        event_handlers = EventHandlerRegister()
        mock = mocker.Mock()
        mock.side_effect = Exception("Help im erroring")

        @event_handlers.register(event_type=DummyEventType.TEST)
        def handler(event):
            mock(event.data["message"])

        event = Event.objects.create(
            type=DummyEventType.TEST, data={"message": "test"}, created_by=admin_user
        )

        event_handlers.handle(event)
        mock.assert_called_once_with("test")

        log = event.handler_logs.get()
        assert log.status == EventHandlerLog.Status.FAILED
        assert log.message == "Help im erroring"

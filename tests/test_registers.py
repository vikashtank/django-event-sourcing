from django_event_sourcing.models import Event

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

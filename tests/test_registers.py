from django_event_sourcing.conditions import Condition
from django_event_sourcing.models import Event, EventHandlerLog, EventSideEffectLog
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

    def test_handles_multiple_event_types(self):
        event_handlers = EventHandlerRegister()

        @event_handlers.register(
            event_type=[DummyEventType.TEST, DummyEventType.TEST_ANOTHER]
        )
        def handler(event):
            pass

        assert handler in event_handlers.handlers[DummyEventType.TEST]
        assert handler in event_handlers.handlers[DummyEventType.TEST_ANOTHER]

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
        assert log.message == "Exception('Help im erroring')"

    def test_handles_side_effects(self, admin_user, mocker):
        event_handlers = EventHandlerRegister()
        mock = mocker.Mock()
        mock.return_value = "result"

        side_effect_mock = mocker.Mock()

        def side_effect(result):
            return side_effect_mock(result)

        @event_handlers.register(event_type=DummyEventType.TEST)
        @event_handlers.register_side_effect(side_effect)
        def handler(event):
            return mock(event.data["message"])

        event = Event.objects.create(
            type=DummyEventType.TEST, data={"message": "test"}, created_by=admin_user
        )

        event_handlers.handle(event)
        mock.assert_called_once_with("test")
        side_effect_mock.assert_called_once_with("result")

        log = event.handler_logs.get()
        assert log.status == EventHandlerLog.Status.SUCCESS

        side_effect_log = log.side_effect_logs.get()
        assert side_effect_log.status == EventSideEffectLog.Status.SUCCESS

    def test_can_skip_side_effects(self, admin_user, mocker):
        event_handlers = EventHandlerRegister()
        mock = mocker.Mock()
        mock.return_value = "result"

        side_effect_mock = mocker.Mock()

        def side_effect(result):
            return side_effect_mock(result)

        @event_handlers.register(event_type=DummyEventType.TEST)
        @event_handlers.register_side_effect(side_effect)
        def handler(event):
            return mock(event.data["message"])

        event = Event.objects.create(
            type=DummyEventType.TEST, data={"message": "test"}, created_by=admin_user
        )

        event_handlers.handle(event, skip_side_effects=True)
        mock.assert_called_once_with("test")
        side_effect_mock.assert_not_called()

        log = event.handler_logs.get()
        assert log.status == EventHandlerLog.Status.SUCCESS

        assert log.side_effect_logs.count() == 0

    def test_skips_side_effects_when_handler_fails(self, admin_user, mocker):
        event_handlers = EventHandlerRegister()
        mock = mocker.Mock()
        mock.side_effect = Exception("Help im erroring")

        side_effect_mock = mocker.Mock()

        def side_effect(result):
            return side_effect_mock(result)

        @event_handlers.register(event_type=DummyEventType.TEST)
        @event_handlers.register_side_effect(side_effect)
        def handler(event):
            return mock(event.data["message"])

        event = Event.objects.create(
            type=DummyEventType.TEST, data={"message": "test"}, created_by=admin_user
        )

        event_handlers.handle(event)
        mock.assert_called_once_with("test")
        side_effect_mock.assert_not_called()

        log = event.handler_logs.get()
        assert log.status == EventHandlerLog.Status.FAILED

        assert log.side_effect_logs.count() == 0

    def test_skips_side_effect_with_failing_conditions(self, admin_user, mocker):
        event_handlers = EventHandlerRegister()
        mock = mocker.Mock()
        mock.return_value = "result"

        side_effect_mock = mocker.Mock()

        def side_effect(result):
            return side_effect_mock(result)

        class TestCondition(Condition):
            def has_condition(self, event):
                return False

        @event_handlers.register(event_type=DummyEventType.TEST)
        @event_handlers.register_side_effect(side_effect, condition=TestCondition)
        def handler(event):
            return mock(event.data["message"])

        event = Event.objects.create(
            type=DummyEventType.TEST, data={"message": "test"}, created_by=admin_user
        )

        event_handlers.handle(event)
        mock.assert_called_once_with("test")
        side_effect_mock.assert_not_called()

        log = event.handler_logs.get()
        assert log.status == EventHandlerLog.Status.SUCCESS

        side_effect_log = log.side_effect_logs.get()
        assert side_effect_log.status == EventSideEffectLog.Status.SKIPPED

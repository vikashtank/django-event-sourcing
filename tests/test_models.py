from django_event_sourcing.models import EventTypeRegister

from .event_types import DummyEventType


class TestEventType:

    def test_fully_qualified_value(self):
        assert DummyEventType.TEST.fully_qualified_value == 'dummy.test'


class TestEventTypeRegister:

    def test_populates_event_types(self, settings):
        register = EventTypeRegister(settings.EVENT_TYPES)
        assert register['dummy.test'] == DummyEventType.TEST

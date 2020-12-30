from django_event_sourcing.models import EventType


class DummyEventType(EventType):
    TEST = 'test'

    def get_namespace(self):
        return 'dummy'


class TestEventType:

    def test_fully_qualified_value(self):
        assert DummyEventType.TEST.fully_qualified_value == 'dummy.test'

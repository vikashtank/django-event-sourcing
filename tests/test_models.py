from .event_types import DummyEventType


class TestEventType:

    def test_fully_qualified_value(self):
        assert DummyEventType.TEST.fully_qualified_value == 'dummy.test'

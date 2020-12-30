import pytest

from django_event_sourcing.models import EventTypeField, EventTypeRegister

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

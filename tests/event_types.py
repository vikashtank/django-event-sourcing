from django_event_sourcing.models import EventType


class DummyEventType(EventType):
    TEST = "test"
    TEST_ANOTHER = "test_another"

    def get_namespace(self):
        return "dummy"

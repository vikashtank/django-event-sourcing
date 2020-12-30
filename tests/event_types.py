from django_event_sourcing.models import EventType


class DummyEventType(EventType):
    TEST = 'test'

    def get_namespace(self):
        return 'dummy'

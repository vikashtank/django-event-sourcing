import collections

from django.utils.module_loading import import_string


class EventTypeRegister(collections.UserDict):
    """A dictionary mapping fully qualified event type values with the event type."""

    def __init__(self, event_type_classes):
        super().__init__()
        for event_type_class in event_type_classes:
            event_type_enum = import_string(event_type_class)
            for event_type in event_type_enum:
                self.data[event_type.fully_qualified_value] = event_type


class EventHandlerRegister:
    """Stores event handlers."""

    def __init__(self):
        self.handlers = collections.defaultdict(lambda: [])

    def register(self, *, event_type):
        def decorator(f):
            self.handlers[event_type].append(f)

        return decorator

    def handle(self, event):
        for handler in self.handlers[event.type]:
            handler(event)

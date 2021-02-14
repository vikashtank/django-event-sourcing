import collections
from collections.abc import Iterable

from django.utils.module_loading import import_string

from .models import EventType


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
        self.side_effects = collections.defaultdict(lambda: [])

    def register(self, *, event_type):
        def decorator(f):
            if isinstance(event_type, EventType):
                self.handlers[event_type].append(f)
            elif isinstance(event_type, Iterable):
                for type in event_type:
                    self.handlers[type].append(f)
            else:
                raise TypeError(f"Unknown event type: {event_type}")

            return f

        return decorator

    def register_side_effect(self, *, side_effect):
        def decorator(f):
            self.side_effects[f].append(side_effect)
            return f

        return decorator

    def handle(self, event, skip_side_effects=False):
        for handler in self.handlers[event.type]:
            handler_log = event.handler_logs.create_from_function(function=handler)
            try:
                result = handler(event)
                handler_log.status = handler_log.Status.SUCCESS
                handler_log.message = str(result)
            except Exception as error:
                handler_log.status = handler_log.Status.FAILED
                handler_log.message = repr(error)
            finally:
                handler_log.save()

            if skip_side_effects or handler_log.status == handler_log.Status.FAILED:
                continue

            for side_effect in self.side_effects[handler]:
                side_effect_log = handler_log.side_effect_logs.create_from_function(
                    function=side_effect
                )
                try:
                    result = side_effect(result)
                    side_effect_log.status = handler_log.Status.SUCCESS
                    side_effect_log.message = str(result)
                except Exception as error:
                    side_effect_log.status = handler_log.Status.FAILED
                    side_effect_log.message = repr(error)
                finally:
                    side_effect_log.save()

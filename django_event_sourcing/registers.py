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

    def _run_event_function(self, log, function, *args, **kwargs):
        result = None
        try:
            result = function(*args, **kwargs)
            log.status = log.Status.SUCCESS
            log.message = str(result)
        except Exception as error:
            log.status = log.Status.FAILED
            log.message = repr(error)
        finally:
            log.save()

        return result

    def handle(self, event, skip_side_effects=False):
        for handler in self.handlers[event.type]:
            handler_log = event.handler_logs.create_from_function(function=handler)
            result = self._run_event_function(handler_log, handler, event)

            if skip_side_effects or handler_log.failed:
                continue

            for side_effect in self.side_effects[handler]:
                side_effect_log = handler_log.side_effect_logs.create_from_function(
                    function=side_effect
                )
                self._run_event_function(side_effect_log, side_effect, result)

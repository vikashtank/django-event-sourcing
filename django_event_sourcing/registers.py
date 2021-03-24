import collections
from collections.abc import Iterable

from django.utils.module_loading import import_string

from .models import EventType, EventSideEffectLog


class EventTypeRegister(collections.UserDict):
    """A dictionary mapping fully qualified event type values with the event type."""

    def __init__(self, event_type_classes):
        super().__init__()
        for event_type_class in event_type_classes:
            event_type_enum = import_string(event_type_class)
            for event_type in event_type_enum:
                self.data[event_type.fully_qualified_value] = event_type


RegisteredSideEffect = collections.namedtuple(
    "RegisteredSideEffect", field_names=("callable", "condition")
)


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

    def register_side_effect(self, callable, *, condition=None):
        def decorator(f):
            self.side_effects[f].append(RegisteredSideEffect(callable, condition))
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

            for registered_side_effect in self.side_effects[handler]:
                condition_class = registered_side_effect.condition
                should_run = (
                    condition_class().has_condition(event) if condition_class else True
                )
                status = (
                    EventSideEffectLog.Status.PROCESSING
                    if should_run
                    else EventSideEffectLog.Status.SKIPPED
                )
                side_effect_log = handler_log.side_effect_logs.create_from_function(
                    function=registered_side_effect.callable, status=status
                )

                if should_run:
                    self._run_event_function(
                        side_effect_log, registered_side_effect.callable, result
                    )

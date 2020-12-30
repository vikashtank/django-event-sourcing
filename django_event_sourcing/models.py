import collections
import enum
import uuid

from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string


class EventType(str, enum.Enum):
    """Represents the type of an event."""

    @property
    def fully_qualified_value(self):
        return '.'.join((self.get_namespace(),  self.value))


class EventTypeRegister(collections.UserDict):
    """A dictionary mapping fully qualified event type values with the event type."""

    def __init__(self, event_type_classes):
        super().__init__()
        for event_type_class in event_type_classes:
            event_type_enum = import_string(event_type_class)
            for event_type in event_type_enum:
                self.data[event_type.fully_qualified_value] = event_type


class Event(models.Model):
    """Represents an action that will happen."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    raw_type = models.CharField(max_length=255, db_index=True)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="events")

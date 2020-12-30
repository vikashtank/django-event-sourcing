import enum

from django.db import models


class EventType(str, enum.Enum):
    """Represents the type of an event."""

    @property
    def fully_qualified_value(self):
        return '.'.join((self.get_namespace(),  self.value))


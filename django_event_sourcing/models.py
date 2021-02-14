import enum
import uuid

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from .globals import get_event_handler_register, get_event_type_register


class EventType(str, enum.Enum):
    """Represents the type of an event."""

    @property
    def fully_qualified_value(self):
        return self.get_namespace() + "." + self.value

    def __hash__(self):
        return hash(self.fully_qualified_value)


class EventTypeField(models.CharField):
    """Stores the fully qualified value of an event type."""

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 255
        kwargs["db_index"] = True
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["max_length"]
        del kwargs["db_index"]
        return name, path, args, kwargs

    def from_db_value(self, fully_qualified_value, *args, **kwargs):
        return get_event_type_register()[fully_qualified_value]

    def to_python(self, fully_qualified_value):
        if isinstance(fully_qualified_value, EventType):
            return fully_qualified_value

        return get_event_type_register()[fully_qualified_value]

    def get_prep_value(self, event_type):
        return event_type.fully_qualified_value


class EventManager(models.Manager):
    def create_and_handle(self, **kwargs):
        event = self.create(**kwargs)
        result = event.handle()
        return event, result


class ModelJSONEncoder(DjangoJSONEncoder):
    """Encodes a model by getting the primary key."""

    def default(self, obj):
        if isinstance(obj, models.Model):
            return obj.pk
        return super().default(obj)


class Event(models.Model):
    """Represents an action that will happen."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = EventTypeField()
    data = models.JSONField(encoder=ModelJSONEncoder)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="events"
    )

    objects = EventManager()

    def handle(self):
        self.refresh_from_db()  # To ensure we haven't got any old references.
        return get_event_handler_register().handle(self)


class EventHandlerLogManager(models.Manager):
    def create_from_function(self, *, function, **kwargs):
        return self.create(**kwargs, name=function.__name__)


class EventHandlerLog(models.Model):
    class Status(models.TextChoices):
        PROCESSING = "processing"
        FAILED = "failed"
        SUCCESS = "success"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event, on_delete=models.PROTECT, related_name="handler_logs"
    )
    status = models.CharField(
        choices=Status.choices, max_length=12, db_index=True, default=Status.PROCESSING
    )
    name = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EventHandlerLogManager()

    @property
    def failed(self):
        return self.status == self.Status.FAILED


class EventSideEffectLog(models.Model):
    class Status(models.TextChoices):
        PROCESSING = "processing"
        FAILED = "failed"
        SUCCESS = "success"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    handler_log = models.ForeignKey(
        EventHandlerLog, on_delete=models.PROTECT, related_name="side_effect_logs"
    )
    status = models.CharField(
        choices=Status.choices, max_length=12, db_index=True, default=Status.PROCESSING
    )
    name = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EventHandlerLogManager()

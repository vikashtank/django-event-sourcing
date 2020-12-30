from django.conf import settings

from .registers import EventHandlerRegister, EventTypeRegister


event_type_register = None
event_handler_register = None


def get_event_type_register():
    global event_type_register

    if event_type_register is None:
        event_type_register = EventTypeRegister(settings.EVENT_TYPES)

    return event_type_register


def get_event_handler_register():
    global event_handler_register

    if event_handler_register is None:
        event_handler_register = EventHandlerRegister()

    return event_handler_register

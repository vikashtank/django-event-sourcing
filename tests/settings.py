INSTALLED_APPS = (
    'django_event_sourcing',

    'django.contrib.auth',
    'django.contrib.contenttypes',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

SECRET_KEY = 'This is a SECRET_KEY'


EVENT_TYPES = [
    'tests.event_types.DummyEventType',
]

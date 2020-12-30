INSTALLED_APPS = (
    'django_event_sourcing',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

SECRET_KEY = 'This is a SECRET_KEY'

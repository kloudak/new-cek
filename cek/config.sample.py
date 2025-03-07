SECRET_KEY = '_some_secret_random_string_'
STATIC_URL = 'static/'
DEBUG = True
ALLOWED_HOSTS = []
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cek',                 
        'USER': '_DB_username_',
        'PASSWORD': '_DB_password_',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
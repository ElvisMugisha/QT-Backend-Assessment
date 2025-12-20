from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DJANGO_DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['*']  # Nginx will filter hosts (or use config('ALLOWED_HOSTS', cast=Csv()))

# Application definition
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',  # Required for AbstractBaseUser
    'apps.accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'apps.accounts.middleware.MTLSAuthenticationMiddleware',
]

ROOT_URLCONF = 'qt_assessment.urls'

WSGI_APPLICATION = 'qt_assessment.wsgi.application'

# Database
# Using SQLite for dev convenience/running tests without docker temporarily
# Will be overridden by Docker envs for Postgres
# Database

if config('DATABASE', default='sqlite') == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': config('SQL_ENGINE'),
            'NAME': config('SQL_DATABASE'),
            'USER': config('SQL_USER'),
            'PASSWORD': config('SQL_PASSWORD'),
            'HOST': config('SQL_HOST'),
            'PORT': config('SQL_PORT'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# User definition
AUTH_USER_MODEL = 'accounts.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Logging (Explicit and simple)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

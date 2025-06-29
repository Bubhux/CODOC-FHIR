import os

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Database routers
# https://docs.djangoproject.com/en/dev/topics/db/multi-db/#automatic-database-routing
DATABASE_ROUTERS = []

# Database
# https://docs.djangoproject.com/en/dev//ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(os.path.dirname(os.path.abspath(__file__)), "db.sqlite3"),
    }
}

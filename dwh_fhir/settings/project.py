# fhir-interview-test-main/dwh_fhir/settings/project.py
import os
import sys
from pathlib import Path

from django.db.models import options

VERSION = os.getenv("DJANGO_VERSION", "dev")

# Common paths
SETTING_DIR = Path(__file__).resolve()
BASE_DIR = SETTING_DIR.parent.parent.parent
APP_DIR = BASE_DIR / "apps"

# Running 'manage.py test' or 'pytest'
TESTING = (len(sys.argv) > 1 and sys.argv[1] == "test" in sys.argv) or "pytest" in sys.modules

# Base URLs
BASE_URL = os.getenv("DJANGO_BASE_URL", "")

# Allows to define more attributes in Models' Meta class.
options.DEFAULT_NAMES += ()

# Display whole SQL query when using `shell_plus`
SHELL_PLUS_PRINT_SQL_TRUNCATE = None

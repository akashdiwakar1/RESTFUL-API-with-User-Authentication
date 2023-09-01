from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# code
import os
import sys
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))
sys.path.append(BASE_DIR)

# Handling the ModuleNotFoundError
try:
    from firstapp.main import Base
except ModuleNotFoundError:
    # Fallback to models if firstapp.main is not found
    from firstapp.models import Base

# This is the Alembic Config object, which provides
# Access to the values within the .ini file in use.
config = context.config

# Making a connection
config.set_main_option('sqlalchemy.url', os.environ['DATABASE_URL'])

fileConfig(config.config_file_name)

def run_migrations_offline():
    pass

def run_migrations_online():
    pass

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

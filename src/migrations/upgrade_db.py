import os
from alembic import command as alembic_command
from alembic.config import Config
def run_migrations(app_dir):
    config = Config(os.path.join(app_dir, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(app_dir, "alembic"))
    alembic_command.upgrade(config, "head")
if __name__ == "__main__":
    run_migrations(os.path.dirname(__file__))
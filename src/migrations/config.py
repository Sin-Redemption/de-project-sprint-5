import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from pydantic import BaseSettings, PostgresDsn, validator

# Для локального использования dot-env, на сервере данные переменные могут быть экспортированы в переменные окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

class Settings(BaseSettings):
    # Использую конфигураци с локального GP
    DATABASE_URI: PostgresDsn = os.environ.get("ALEMBIC_URL", "postgresql://gpadmin:gpadmin@localhost:5432/public")
    DATABASE_ROLE: str = os.environ.get("ALEMBIC_ROLE", "gpadmin")
    ALEMBIC_TABLE_NAME: str = os.environ.get("ALEMBIC_TABLE", "alembic_version")
    @validator("DATABASE_URI")
    def quote(cls, value, values, config, field):  # noQA
        kwargs = dict(
            scheme="postgresql",
            user=value.user,
            # Replace % need only alembic
            password=quote_plus(value.password).replace("%", "%%"),
            host=value.host,
            port=value.port,
            path=value.path,
            query=value.query
        )
        url = PostgresDsn.build(**kwargs)
        return PostgresDsn(url, **kwargs)
settings = Settings()
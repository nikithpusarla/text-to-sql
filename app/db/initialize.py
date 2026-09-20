from __future__ import annotations

from pathlib import Path

from psycopg import sql

from app.config import settings
from app.db.connection import get_admin_connection

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def initialize_schema() -> None:
    """Create application tables and read-only permissions without changing data."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_admin_connection() as connection, connection.cursor() as cursor:
        cursor.execute(schema_sql)
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = %s",
            (settings.postgres_readonly_user,),
        )
        if cursor.fetchone() is None:
            cursor.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE"
                ).format(
                    sql.Identifier(settings.postgres_readonly_user),
                    sql.Literal(settings.postgres_readonly_password),
                )
            )
        cursor.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(settings.postgres_db),
                sql.Identifier(settings.postgres_readonly_user),
            )
        )
        cursor.execute(
            sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(
                sql.Identifier(settings.postgres_readonly_user),
            )
        )
        cursor.execute(
            sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA public TO {}").format(
                sql.Identifier(settings.postgres_readonly_user),
            )
        )
        cursor.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {}").format(
                sql.Identifier(settings.postgres_readonly_user),
            )
        )
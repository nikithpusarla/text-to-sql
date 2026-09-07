from __future__ import annotations

import os
from typing import Any

import psycopg

from app.config import settings


def get_connection_kwargs() -> dict[str, Any]:
    return {
        "dbname": settings.postgres_db,
        "user": settings.postgres_readonly_user,
        "password": settings.postgres_readonly_password,
        "host": settings.postgres_host,
        "port": settings.postgres_port,
        "autocommit": True,
    }


def get_connection():
    return psycopg.connect(**get_connection_kwargs())

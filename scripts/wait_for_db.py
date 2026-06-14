"""Wait until the configured MariaDB/MySQL database is reachable.

This is intentionally small and dependency-light. It uses mysqlclient, which is
already required by the Django project. The script prevents the app container
from running migrations while the database container is still initializing.
"""

from __future__ import annotations

import os
import sys
import time

import MySQLdb


HOST = os.getenv("DB_HOST", "db")
PORT = int(os.getenv("DB_PORT", "3306"))
USER = os.getenv("DB_USER", "enterprise_dms_user")
PASSWORD = os.getenv("DB_PASSWORD", "change-app-password")
DATABASE = os.getenv("DB_APP_NAME", "enterprise_dms_appdata")
MAX_ATTEMPTS = int(os.getenv("DB_WAIT_ATTEMPTS", "60"))
SLEEP_SECONDS = float(os.getenv("DB_WAIT_SLEEP", "2"))


def main() -> int:
    print(f"Waiting for database {HOST}:{PORT}/{DATABASE}...", flush=True)

    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            connection = MySQLdb.connect(
                host=HOST,
                port=PORT,
                user=USER,
                passwd=PASSWORD,
                db=DATABASE,
                connect_timeout=5,
            )
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            connection.close()
            print("Database is ready.", flush=True)
            return 0
        except Exception as exc:  # noqa: BLE001 - startup diagnostics only
            last_error = exc
            print(
                f"Database not ready yet ({attempt}/{MAX_ATTEMPTS}): {exc}",
                flush=True,
            )
            time.sleep(SLEEP_SECONDS)

    print(f"Database did not become ready. Last error: {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

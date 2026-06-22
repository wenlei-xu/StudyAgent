"""Database migration quick command — runs Alembic migrations.

Usage:
    python scripts/migrate.py              # upgrade to latest
    python scripts/migrate.py downgrade    # rollback one revision
    python scripts/migrate.py revision     # create a new migration
"""

import sys
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "app" / "db" / "migrations"


def run_alembic(cmd: list[str]) -> None:
    subprocess.run(
        ["alembic", "-c", str(MIGRATIONS_DIR / "alembic.ini"), *cmd],
        cwd=str(PROJECT_ROOT),
        check=True,
    )


def main() -> None:
    if not (MIGRATIONS_DIR / "alembic.ini").exists():
        print("alembic.ini not found — run 'alembic init' first")
        sys.exit(1)

    arg = sys.argv[1] if len(sys.argv) > 1 else "upgrade"

    if arg == "downgrade":
        run_alembic(["downgrade", "-1"])
    elif arg == "revision":
        msg = sys.argv[2] if len(sys.argv) > 2 else "auto"
        run_alembic(["revision", "--autogenerate", "-m", msg])
    else:
        run_alembic(["upgrade", "head"])


if __name__ == "__main__":
    main()

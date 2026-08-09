"""Read-only schema compatibility report; never stamps or alters a database."""
import sys
from pathlib import Path

# Support the documented `python scripts/check_schema.py` invocation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect
from app.config.database import Base, engine
import app.models  # noqa: F401

def main() -> int:
    inspector = inspect(engine)
    actual = set(inspector.get_table_names())
    expected = set(Base.metadata.tables)
    missing = sorted(expected - actual)
    unmanaged = sorted(actual - expected - {"alembic_version"})
    mismatches = []
    for table in sorted(expected & actual):
        actual_columns = {item["name"] for item in inspector.get_columns(table)}
        expected_columns = set(Base.metadata.tables[table].columns.keys())
        missing_columns = expected_columns - actual_columns
        unexpected_columns = actual_columns - expected_columns
        if missing_columns:
            mismatches.append(f"{table}: missing {', '.join(sorted(missing_columns))}")
        if unexpected_columns:
            mismatches.append(f"{table}: unexpected {', '.join(sorted(unexpected_columns))}")
    print("Learnfy AI schema check (read-only)")
    print(f"Missing tables: {', '.join(missing) or 'none'}")
    print(f"Column mismatches: {'; '.join(mismatches) or 'none'}")
    print(f"Unmanaged tables: {', '.join(unmanaged) or 'none'}")
    if missing or mismatches or unmanaged:
        print("DO NOT stamp this database. Back it up and create a reviewed upgrade migration.")
        return 1
    if "alembic_version" in actual:
        print("Schema is already Alembic-managed. Use `alembic current` and `alembic upgrade head`.")
    else:
        print("Schema exactly matches mapped tables. After a backup and human review, run: alembic stamp 20260806_0001")
        print("Then run: alembic upgrade head (this safely applies later constraints such as PayHere payment-ID uniqueness).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

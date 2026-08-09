"""Complete Learnfy AI schema baseline.

Fresh databases only. Existing databases must be inspected with
`python scripts/check_schema.py` before a human chooses whether to stamp.
"""
from alembic import op
from sqlalchemy import inspect
from app.config.database import Base
import app.models  # noqa: F401

revision = "20260806_0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    existing = set(inspect(bind).get_table_names()) - {"alembic_version"}
    if existing:
        raise RuntimeError(
            "Refusing to apply the baseline to a non-empty untracked database. "
            "Back it up and run `python scripts/check_schema.py`; never stamp an unknown schema."
        )
    Base.metadata.create_all(bind=bind, checkfirst=False)

def downgrade() -> None:
    raise RuntimeError("Baseline downgrade is intentionally disabled to protect data")

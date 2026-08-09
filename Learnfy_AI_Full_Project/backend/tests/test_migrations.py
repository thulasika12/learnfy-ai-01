from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.config.settings import settings

BACKEND_ROOT = Path(__file__).resolve().parents[1]

def config_for(database_url: str, monkeypatch) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    monkeypatch.setattr(settings, "DATABASE_URL", database_url)
    return config

def test_fresh_migration_is_repeat_safe(tmp_path, monkeypatch):
    url = f"sqlite:///{(tmp_path / 'fresh.db').as_posix()}"
    config = config_for(url, monkeypatch)
    command.upgrade(config, "head")
    first_tables = set(inspect(create_engine(url)).get_table_names())
    command.upgrade(config, "head")
    assert set(inspect(create_engine(url)).get_table_names()) == first_tables
    assert "alembic_version" in first_tables
    assert "daily_ai_usage" in first_tables

def test_baseline_refuses_unknown_nonempty_database(tmp_path, monkeypatch):
    url = f"sqlite:///{(tmp_path / 'unknown.db').as_posix()}"
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE unrelated_legacy_data (id INTEGER PRIMARY KEY)"))
    with pytest.raises(RuntimeError, match="Refusing to apply the baseline"):
        command.upgrade(config_for(url, monkeypatch), "head")

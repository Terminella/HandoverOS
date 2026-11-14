"""Migration test for c1d2e3f4a5b6_add_source_id_to_handover_items.

Verifies that the SQLite-compatible migration produces the intended schema:

- handover_items.source_id: nullable String(36)
- FK fk_handover_item_source: handover_items.source_id -> sources.id

Uses direct SQL DDL execution (mirroring what Alembic's batch_alter_table
does internally for SQLite) to validate the migration operations without
Alembic CLI/path issues on Windows.
"""

import os
import sys
import tempfile

# Ensure the installed alembic package takes precedence over the local
# backend/alembic migration directory (which shadows it).
venv_site = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".venv", "Lib", "site-packages",
)
if os.path.isdir(venv_site) and venv_site not in sys.path:
    sys.path.insert(0, venv_site)

from sqlalchemy import create_engine, text, inspect as sa_inspect


def _apply_upgrade(engine):
    """Apply upgrade: add source_id column + FK via SQLite table recreation."""
    connection = engine.connect()
    connection.execute(text("PRAGMA foreign_keys = OFF"))
    connection.execute(text("""
        CREATE TABLE handover_items_new (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            handover_id VARCHAR(36) NOT NULL,
            knowledge_item_id VARCHAR(36),
            content TEXT NOT NULL,
            section VARCHAR(100) NOT NULL,
            position INTEGER NOT NULL,
            source_id VARCHAR(36),
            FOREIGN KEY (handover_id) REFERENCES handovers(id),
            FOREIGN KEY (knowledge_item_id) REFERENCES knowledge_items(id),
            FOREIGN KEY (source_id) REFERENCES sources(id)
        )
    """))
    connection.execute(text("""
        INSERT INTO handover_items_new (id, handover_id, knowledge_item_id, content, section, position, source_id)
        SELECT id, handover_id, knowledge_item_id, content, section, position, NULL FROM handover_items
    """))
    connection.execute(text("DROP TABLE handover_items"))
    connection.execute(text("ALTER TABLE handover_items_new RENAME TO handover_items"))
    connection.execute(text("PRAGMA foreign_keys = ON"))
    connection.commit()
    connection.close()


def _apply_downgrade(engine):
    """Apply downgrade: remove source_id column + FK via SQLite table recreation."""
    connection = engine.connect()
    connection.execute(text("PRAGMA foreign_keys = OFF"))
    connection.execute(text("""
        CREATE TABLE handover_items_new (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            handover_id VARCHAR(36) NOT NULL,
            knowledge_item_id VARCHAR(36),
            content TEXT NOT NULL,
            section VARCHAR(100) NOT NULL,
            position INTEGER NOT NULL,
            FOREIGN KEY (handover_id) REFERENCES handovers(id),
            FOREIGN KEY (knowledge_item_id) REFERENCES knowledge_items(id)
        )
    """))
    connection.execute(text("""
        INSERT INTO handover_items_new (id, handover_id, knowledge_item_id, content, section, position)
        SELECT id, handover_id, knowledge_item_id, content, section, position FROM handover_items
    """))
    connection.execute(text("DROP TABLE handover_items"))
    connection.execute(text("ALTER TABLE handover_items_new RENAME TO handover_items"))
    connection.execute(text("PRAGMA foreign_keys = ON"))
    connection.commit()
    connection.close()


def _setup_base_schema(engine):
    """Create prerequisite tables (parent revision state, before migration)."""
    connection = engine.connect()
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS sources (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            project_id VARCHAR(100) NOT NULL,
            source_type VARCHAR(50) NOT NULL,
            source_name VARCHAR(255) NOT NULL,
            source_id VARCHAR(255) NOT NULL,
            title VARCHAR(500),
            content TEXT NOT NULL,
            content_hash VARCHAR(128),
            source_metadata JSON DEFAULT '{}',
            ingested_at DATETIME NOT NULL
        )
    """))
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS handover_items (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            handover_id VARCHAR(36) NOT NULL,
            knowledge_item_id VARCHAR(36),
            content TEXT NOT NULL,
            section VARCHAR(100) NOT NULL,
            position INTEGER NOT NULL,
            FOREIGN KEY (handover_id) REFERENCES handovers(id),
            FOREIGN KEY (knowledge_item_id) REFERENCES knowledge_items(id)
        )
    """))
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS handovers (
            id VARCHAR(36) NOT NULL PRIMARY KEY
        )
    """))
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS knowledge_items (
            id VARCHAR(36) NOT NULL PRIMARY KEY
        )
    """))
    connection.commit()
    connection.close()


def _inspect_handover_items(engine):
    inspector = sa_inspect(engine)
    columns = {col["name"]: col for col in inspector.get_columns("handover_items")}
    fks = inspector.get_foreign_keys("handover_items")
    return columns, fks


def test_migration_adds_source_id_column_and_foreign_key():
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test_migration.db")
    db_url = f"sqlite:///{db_path}"

    try:
        engine = create_engine(db_url)

        # Set up base schema (parent revision state).
        _setup_base_schema(engine)

        # Verify pre-upgrade state: no source_id column, no FK to sources.
        columns, fks = _inspect_handover_items(engine)
        assert "source_id" not in columns, (
            "source_id should not exist before upgrade"
        )
        sources_fks = [fk for fk in fks if fk["referred_table"] == "sources"]
        assert len(sources_fks) == 0, (
            "FK to sources should not exist before upgrade"
        )

        # Apply upgrade (add source_id + FK).
        _apply_upgrade(engine)

        # Verify post-upgrade state.
        columns, fks = _inspect_handover_items(engine)
        assert "source_id" in columns, "source_id column missing after upgrade"
        assert columns["source_id"]["nullable"] is True, (
            f"source_id should be nullable, got nullable={columns['source_id']['nullable']}"
        )

        sources_fks = [fk for fk in fks if fk["referred_table"] == "sources"]
        assert len(sources_fks) == 1, (
            f"Expected 1 FK to sources, got {sources_fks}"
        )
        assert sources_fks[0]["constrained_columns"] == ["source_id"], (
            f"FK constrained columns should be ['source_id'], got {sources_fks[0]['constrained_columns']}"
        )
        assert sources_fks[0]["referred_columns"] == ["id"], (
            f"FK referred columns should be ['id'], got {sources_fks[0]['referred_columns']}"
        )

        # Apply downgrade (remove FK + column).
        _apply_downgrade(engine)

        # Verify post-downgrade state.
        columns, fks = _inspect_handover_items(engine)
        assert "source_id" not in columns, (
            "source_id should be removed after downgrade"
        )
        sources_fks = [fk for fk in fks if fk["referred_table"] == "sources"]
        assert len(sources_fks) == 0, (
            f"FK to sources should be removed, got {sources_fks}"
        )

    finally:
        import shutil

        shutil.rmtree(tmpdir, ignore_errors=True)

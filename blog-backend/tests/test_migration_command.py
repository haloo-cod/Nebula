"""独立迁移命令的隔离进程回归，不连接默认数据库或启动 Web 应用。"""

from contextlib import closing
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from uuid import UUID


BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATION_VERSION = "20261023_auth_identity_uuid"


def run_migration(root, **overrides):
    """为子进程指定临时数据库和全部本地存储目录。"""
    environment = os.environ.copy()
    environment.update({
        "DATABASE_URL": f"sqlite+aiosqlite:///{(root / 'legacy.db').as_posix()}",
        "ENVIRONMENT": "production",
        "DEBUG": "false",
        "SECRET_KEY": "migration-command-secret-key-for-isolated-tests",
        "ADMIN_PASSWORD": "migration-command-admin-password",
        "ANALYTICS_HASH_SALT": "migration-command-analytics-salt-for-isolated-tests",
        "COOKIE_SECURE": "true",
        "FRONTEND_URL": "https://migration.example.test",
        "CORS_ORIGINS": '["https://migration.example.test"]',
        "DATA_DIR": str(root / "data"),
        "CONTENT_DIR": str(root / "content"),
        "UPLOAD_DIR": str(root / "uploads"),
        "BOOK_ARCHIVE_DIR": str(root / "uploads" / "book-archives"),
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    environment.update(overrides)
    return subprocess.run(
        [sys.executable, "-m", "scripts.migrate"],
        cwd=BACKEND_DIR,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )


def legacy_database(path):
    """保留完整旧用户资料及两种刷新会话，覆盖原值和撤销时间的保留。"""
    with closing(sqlite3.connect(path)) as database:
        database.row_factory = sqlite3.Row
        database.executescript("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY, username VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(200) NOT NULL, is_admin BOOLEAN NOT NULL,
                email VARCHAR(320), display_name VARCHAR(100) NOT NULL,
                avatar_url VARCHAR(500) NOT NULL, github_id VARCHAR(100),
                email_verified BOOLEAN NOT NULL, is_active BOOLEAN NOT NULL,
                last_login_at DATETIME, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL
            );
            INSERT INTO users VALUES (
                41, 'legacy-owner', 'preserved-password-hash', 0,
                'owner@example.test', 'Original Owner', '/uploads/images/original.png', '12345',
                1, 1, '2026-01-03 04:05:06', '2024-01-01 00:00:00', '2026-01-02 00:00:00'
            );
            CREATE TABLE auth_sessions (
                id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
                token_hash VARCHAR(64) NOT NULL UNIQUE, expires_at DATETIME NOT NULL,
                revoked_at DATETIME, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL
            );
        """)
        database.executemany(
            "INSERT INTO auth_sessions VALUES (?, 41, ?, '2099-01-01 00:00:00', ?, "
            "'2024-01-01 00:00:00', '2024-01-01 00:00:00')",
            [(7, "a" * 64, None), (8, "b" * 64, "2025-01-01 00:00:00")],
        )
        database.commit()
        return dict(database.execute("SELECT * FROM users").fetchone())


def test_command_migrates_legacy_database_once_without_startup_side_effects(tmp_path):
    """CLI 保留数据与文件；重跑不改变 UUID、旧撤销时间或新会话。"""
    database_path = tmp_path / "legacy.db"
    original_user = legacy_database(database_path)
    untouched_database = tmp_path / "untouched.db"
    legacy_database(untouched_database)
    untouched_bytes = untouched_database.read_bytes()
    resources = {
        tmp_path / "data" / "friends.json": b'[{"id": 99, "name": "preserved-copy"}]\n',
        tmp_path / "content" / "posts" / "original.md": b"original content\n",
        tmp_path / "uploads" / "images" / "original.png": b"original media",
    }
    for path, content in resources.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    first = run_migration(tmp_path, ENVIRONMENT="development", DEBUG="true")
    assert first.returncode == 0, first.stdout + first.stderr
    with closing(sqlite3.connect(database_path)) as database:
        database.row_factory = sqlite3.Row
        users = [dict(row) for row in database.execute("SELECT * FROM users ORDER BY id")]
        assert [user["id"] for user in users] == [41]
        user = users[0]
        assert {name: user[name] for name in original_user} == original_user
        auth_id = user["auth_id"]
        assert str(UUID(auth_id)) == auth_id and UUID(auth_id).version == 4
        old_sessions = {
            row["id"]: dict(row)
            for row in database.execute("SELECT * FROM auth_sessions ORDER BY id")
        }
        assert old_sessions[7]["revoked_at"] is not None
        assert old_sessions[8]["revoked_at"] == "2025-01-01 00:00:00"
        assert old_sessions[7]["auth_id"] == old_sessions[8]["auth_id"] == ""
        marker = tuple(database.execute("SELECT version, applied_at FROM schema_migrations").fetchone())
        assert marker[0] == MIGRATION_VERSION and marker[1] is not None
        database.execute(
            "INSERT INTO auth_sessions (id, user_id, auth_id, token_hash, expires_at, revoked_at, "
            "created_at, updated_at) VALUES (9, 41, ?, ?, '2099-01-01 00:00:00', NULL, "
            "'2026-10-23 00:00:00', '2026-10-23 00:00:00')",
            (auth_id, "c" * 64),
        )
        database.commit()

    second = run_migration(tmp_path)
    assert second.returncode == 0, second.stdout + second.stderr
    with closing(sqlite3.connect(database_path)) as database:
        database.row_factory = sqlite3.Row
        assert database.execute("SELECT auth_id FROM users WHERE id = 41").fetchone()[0] == auth_id
        assert [dict(row) for row in database.execute("SELECT * FROM auth_sessions WHERE id < 9 ORDER BY id")] == list(old_sessions.values())
        assert database.execute("SELECT revoked_at FROM auth_sessions WHERE id = 9").fetchone()[0] is None
        assert [tuple(row) for row in database.execute("SELECT version, applied_at FROM schema_migrations")] == [marker]

    output = first.stdout + first.stderr + second.stdout + second.stderr
    for private_value in (auth_id, original_user["password_hash"], "a" * 64, "b" * 64):
        assert private_value not in output
    assert untouched_database.read_bytes() == untouched_bytes
    assert {path: path.read_bytes() for path in resources} == resources


def test_command_rejects_unsafe_production_config_without_changing_database(tmp_path):
    """配置错误在迁移前退出，既不改库也不泄漏配置值。"""
    path = tmp_path / "legacy.db"
    legacy_database(path)
    before = path.read_bytes()
    secret = "private-short-key"
    result = run_migration(tmp_path, SECRET_KEY=secret)
    assert result.returncode != 0
    assert path.read_bytes() == before
    assert secret not in result.stdout + result.stderr


def test_command_reports_database_failure_without_dumping_connection_details(tmp_path):
    """真实数据库打开失败以非零退出，错误输出不包含私有连接路径。"""
    path = tmp_path / "private-database.db"
    path.mkdir()
    result = run_migration(tmp_path, DATABASE_URL=f"sqlite+aiosqlite:///{path.as_posix()}")
    assert result.returncode != 0
    assert path.is_dir()
    assert path.name not in result.stdout + result.stderr
    assert str(path) not in result.stdout + result.stderr


def test_command_rolls_back_schema_uuid_and_session_changes_on_failure(tmp_path):
    """已有 UUID 冲突时整体回滚，不能留下版本记录、部分新表或会话撤销。"""
    path = tmp_path / "legacy.db"
    original = legacy_database(path)
    identity = "45e7dcb5-f931-4f85-9f37-bf445bace732"
    with closing(sqlite3.connect(path)) as database:
        database.execute("ALTER TABLE users ADD COLUMN auth_id VARCHAR(36) NOT NULL DEFAULT ''")
        database.execute("UPDATE users SET auth_id = ?", (identity,))
        second = dict(original, id=42, username="second-owner", email="second@example.test", github_id="54321", auth_id=identity)
        columns = ",".join(second)
        placeholders = ",".join("?" for _ in second)
        database.execute(f"INSERT INTO users ({columns}) VALUES ({placeholders})", tuple(second.values()))
        database.commit()
        before = {name: database.execute(f"SELECT * FROM {name} ORDER BY id").fetchall()
                  for name in ("users", "auth_sessions")}
    result = run_migration(tmp_path)
    assert result.returncode != 0
    assert identity not in result.stdout + result.stderr
    with closing(sqlite3.connect(path)) as database:
        tables = {row[0] for row in database.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )}
        assert tables == set(before)
        assert {name: database.execute(f"SELECT * FROM {name} ORDER BY id").fetchall()
                for name in before} == before

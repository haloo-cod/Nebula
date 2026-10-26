"""正式友链快照的真实文件读写、失败恢复和并发回归。"""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.router import router
from app.config import settings
from app.database import get_db
from app.models import Base
from app.models.friend import Friend
from app.models.user import User
from app.schemas.friend import FriendResponse
from app.services import friend as service
from app.utils.security import create_access_token


@pytest_asyncio.fixture
async def friend_env(tmp_path, monkeypatch):
    """每个 HTTP 请求独立会话，使用临时文件数据库和真实认证。"""
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path / "data")
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'friends.db'}", connect_args={"timeout": 10})
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with sessions() as db:
        db.add_all([
            User(id=1, username="a", email="a@example.com", email_verified=True),
            User(id=2, username="b", email="b@example.com", email_verified=True),
            User(id=3, username="admin", is_admin=True, email_verified=True),
            User(id=4, username="disabled", is_active=False),
        ])
        await db.commit()
        users = {user.username: user for user in (await db.scalars(select(User))).all()}
    app = FastAPI()
    app.include_router(router)

    async def request_db():
        async with sessions() as db:
            yield db

    app.dependency_overrides[get_db] = request_db
    headers = {name: {"Authorization": "Bearer " + create_access_token({"sub": user.auth_id})}
               for name, user in users.items()}
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            yield SimpleNamespace(client=client, sessions=sessions, engine=engine, headers=headers,
                                  path=settings.DATA_DIR / "friends.json", app=app, users=users)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_manual_friend_crud_failure_recovery_and_empty_snapshot(friend_env, monkeypatch):
    env = friend_env
    c, admin = env.client, env.headers["admin"]
    created = await c.post("/api/v1/friends", headers=admin, json={"name": "手工", "url": "legacy-address", "bio": "原介绍"})
    assert created.status_code == 201
    friend_id = created.json()["id"]
    assert json.loads(env.path.read_text("utf-8"))[0]["id"] == friend_id
    old_bytes = env.path.read_bytes()
    original_replace = Path.replace

    def fail_replace(self, target):
        if Path(target) == env.path:
            raise OSError("simulated disk failure")
        return original_replace(self, target)

    monkeypatch.setattr(Path, "replace", fail_replace)
    failed = await c.put(f"/api/v1/friends/{friend_id}", headers=admin, json={"name": "已保存", "rss_url": "https://example.com/rss.xml"})
    assert failed.status_code == 503 and failed.json()["detail"] == "FRIEND_JSON_SYNC_FAILED"
    assert env.path.read_bytes() == old_bytes
    assert not list(env.path.parent.glob(".friends.*.tmp"))
    assert (await c.get("/api/v1/friends")).json()["items"][0]["name"] == "已保存"
    monkeypatch.setattr(Path, "replace", original_replace)
    assert (await c.post("/api/v1/friends/sync-json", headers=admin)).status_code == 204
    snapshot = json.loads(env.path.read_text("utf-8"))
    assert len(snapshot) == 1 and snapshot[0]["name"] == "已保存"
    assert snapshot[0]["rss_url"] == "https://example.com/rss.xml"
    assert (await c.delete(f"/api/v1/friends/{friend_id}", headers=admin)).status_code == 204
    assert env.path.read_bytes() == b"[]\n"


@pytest.mark.asyncio
async def test_snapshot_recovers_missing_corrupt_files_and_ignores_old_session_snapshot(friend_env):
    env = friend_env
    async with env.sessions() as old_session:
        await old_session.execute(select(Friend))
        async with env.sessions() as writer:
            await service.create_friend(writer, "最新", "https://latest.example.com/", sort_order=2)
            await writer.commit()
        await service.sync_friends_json(old_session)
        assert json.loads(env.path.read_text("utf-8"))[0]["name"] == "最新"
        env.path.write_text("broken", encoding="utf-8")
        await service.sync_friends_json(old_session)
        assert json.loads(env.path.read_text("utf-8"))[0]["url"] == "https://latest.example.com/"
        env.path.unlink()
        await service.sync_friends_json(old_session)
        assert json.loads(env.path.read_text("utf-8"))[0]["name"] == "最新"


@pytest.mark.asyncio
async def test_snapshot_lock_precedes_query_and_serializes_committed_writers(friend_env, monkeypatch):
    env = friend_env
    async with env.sessions() as initial:
        await service.sync_friends_json(initial)
    acquired, release = asyncio.Event(), asyncio.Event()
    original_list = service.list_friends
    first = True

    async def controlled_list(db):
        nonlocal first
        if first:
            first = False
            acquired.set()
            await release.wait()
        return await original_list(db)

    monkeypatch.setattr(service, "list_friends", controlled_list)
    async with env.sessions() as snapshot_db, env.sessions() as writer:
        earlier = asyncio.create_task(service.sync_friends_json(snapshot_db))
        await asyncio.wait_for(acquired.wait(), 5)
        await service.create_friend(writer, "并发写入", "https://concurrent.example.com/", sort_order=1)
        await writer.commit()
        later = asyncio.create_task(service.sync_friends_json(writer))
        assert json.loads(env.path.read_text("utf-8")) == []
        release.set()
        while not (earlier.done() and later.done()):
            json.loads(env.path.read_text("utf-8"))
            await asyncio.sleep(0.005)
        await asyncio.gather(earlier, later)
    async with env.sessions() as db:
        expected = [FriendResponse.model_validate(row).model_dump(mode="json") for row in await original_list(db)]
    assert json.loads(env.path.read_text("utf-8")) == expected

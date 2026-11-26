"""密码 UTF-8 边界的真实注册、登录和重置回归。"""

import pytest
from sqlalchemy import select

from app.config import settings
from app.models.user import User
from app.utils.security import hash_password
from tests.test_friend_snapshot import friend_env  # noqa: F401


@pytest.mark.asyncio
@pytest.mark.parametrize("password", ["a" * 73, "汉" * 25])
async def test_overlong_registration_and_reset_are_rejected_without_mutation(friend_env, monkeypatch, password):
    env = friend_env
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION", False)
    async with env.sessions() as db:
        original = await db.get(User, 1)
        original.password_hash = hash_password("Original-password-123")
        await db.commit()
        original_hash = original.password_hash

    registered = await env.client.post("/api/v1/auth/register", json={
        "username": "byte-boundary", "email": "boundary@example.com", "password": password,
    })
    assert registered.status_code == 422
    reset = await env.client.post("/api/v1/users/1/reset-password", headers=env.headers["admin"], json={"password": password})
    assert reset.status_code == 422
    async with env.sessions() as db:
        assert await db.scalar(select(User.id).where(User.username == "byte-boundary")) is None
        assert (await db.get(User, 1)).password_hash == original_hash
    logged_in = await env.client.post("/api/v1/auth/login", json={"username": "a", "password": "Original-password-123"})
    assert logged_in.status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("password", ["a" * 72, "汉" * 24])
async def test_exact_72_byte_password_round_trips_and_is_never_truncated(friend_env, monkeypatch, password):
    env = friend_env
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION", False)
    monkeypatch.setattr(settings, "COOKIE_SECURE", False)
    registered = await env.client.post("/api/v1/auth/register", json={
        "username": "boundary-owner", "email": "boundary-owner@example.com", "password": password,
    })
    assert registered.status_code == 201
    correct = await env.client.post("/api/v1/auth/login", json={"username": "boundary-owner", "password": password})
    assert correct.status_code == 200
    too_long = await env.client.post("/api/v1/auth/login", json={"username": "boundary-owner", "password": password + "x"})
    assert too_long.status_code == 401
    wrong = await env.client.post("/api/v1/auth/login", json={"username": "boundary-owner", "password": "Wrong-password-123"})
    assert wrong.status_code == 401

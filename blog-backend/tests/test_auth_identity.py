"""UUID 账户身份的真实路由、权限、刷新会话与 OAuth 回归。"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit
from uuid import UUID, uuid4

import httpx
import pytest
import pytest_asyncio
from jose import jwt
from sqlalchemy import func, select

from app.api.v1 import auth as auth_api
from app.config import settings
from app.models.comment import Comment
from app.models.user import AuthSession, User
from app.services.schema_migration import migrate_existing_schema
from app.utils.security import (
    ALGORITHM,
    create_access_token,
    create_email_verification_token,
    decode_access_token,
    hash_token,
)
from tests.test_friend_snapshot import friend_env  # noqa: F401

AUTH = "/api/v1/auth"
APPLICATIONS = "/api/v1/friends/applications"
COMMENTS = "/api/v1/comments"
PASSWORD = "Correct-horse-123"
PUBLIC_USER_FIELDS = {
    "id", "username", "is_admin", "email", "display_name", "avatar_url", "email_verified",
}


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def refresh_cookie(token):
    return {"Cookie": f"{auth_api.REFRESH_COOKIE}={token}"}


def access_subject(token):
    """检查服务端实际签发的访问令牌采用规范 UUID，而不是整数或用户名。"""
    payload = decode_access_token(token)
    assert payload is not None and payload["type"] == "access"
    subject = payload["sub"]
    identity = UUID(subject)
    assert identity.version == 4 and str(identity) == subject
    return subject


async def registered(env, username="uuid-owner", email="uuid-owner@example.com"):
    response = await env.client.post(
        f"{AUTH}/register", json={"username": username, "email": email, "password": PASSWORD},
    )
    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"access_token", "token_type", "requires_email_verification", "email"}
    assert body["token_type"] == "bearer" and body["requires_email_verification"] is False
    token = body["access_token"]
    auth_id = access_subject(token)
    headers = bearer(token)
    me = await env.client.get(f"{AUTH}/me", headers=headers)
    assert me.status_code == 200
    user = me.json()
    assert set(user) == PUBLIC_USER_FIELDS
    assert isinstance(user["id"], int) and user["username"] == username
    async with env.sessions() as db:
        stored = await db.get(User, user["id"])
        assert stored is not None and stored.auth_id == auth_id
    refresh_token = env.client.cookies.get(auth_api.REFRESH_COOKIE)
    assert refresh_token
    return SimpleNamespace(
        id=user["id"], auth_id=auth_id, username=username, email=email,
        token=token, headers=headers, refresh_token=refresh_token,
    )


async def private_application(env, owner, site="private"):
    response = await env.client.post(
        APPLICATIONS,
        headers=owner.headers,
        json={
            "name": site,
            "url": f"https://{site}.example.com/",
            "avatar": f"https://{site}.example.com/avatar.png",
            "email": f"private-{site}@example.com",
        },
    )
    assert response.status_code == 201
    return response.json()


async def assert_private_access_denied(env, token):
    for path in (f"{AUTH}/me", f"{APPLICATIONS}/mine"):
        response = await env.client.get(path, headers=bearer(token))
        assert response.status_code == 401


async def assert_comment_readonly(env, token, comment_id, page_key="about"):
    response = await env.client.get(
        COMMENTS, headers=bearer(token), params={"page_key": page_key},
    )
    assert response.status_code == 200
    comment = next(item for item in response.json()["items"] if item["id"] == comment_id)
    assert comment["can_delete"] is False
    deleted = await env.client.delete(f"{COMMENTS}/{comment_id}", headers=bearer(token))
    assert deleted.status_code == 401


@pytest_asyncio.fixture
async def auth_env(friend_env, monkeypatch):
    """沿用文件 SQLite 和独立请求会话；只替换配置与外部服务边界。"""
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION", False)
    monkeypatch.setattr(settings, "COOKIE_SECURE", False)
    monkeypatch.setattr(settings, "FRONTEND_URL", "http://frontend.test")
    monkeypatch.setattr(settings, "GITHUB_CLIENT_ID", "uuid-regression-client")
    monkeypatch.setattr(settings, "GITHUB_CLIENT_SECRET", "uuid-regression-secret")
    monkeypatch.setattr(settings, "GITHUB_CALLBACK_URL", "http://test/api/v1/auth/github/callback")
    # 首次迁移必须在创建登录会话之前完成，避免测试把迁移的一次性撤销当成刷新失败。
    await migrate_existing_schema(friend_env.engine)
    yield friend_env


@pytest_asyncio.fixture
async def reassigned_env(auth_env):
    env = auth_env
    original = await registered(env, "reused-account", "reused@example.com")
    old_numeric = create_access_token({"sub": str(original.id)})
    old_username = create_access_token({"sub": original.username})
    async with env.sessions() as db:
        assert await db.scalar(select(func.max(User.id))) == original.id
    deleted = await env.client.delete(f"/api/v1/users/{original.id}", headers=env.headers["admin"])
    assert deleted.status_code == 204
    await assert_private_access_denied(env, original.token)
    replacement = await registered(env, original.username, original.email)
    assert replacement.id == original.id
    assert replacement.auth_id != original.auth_id
    return SimpleNamespace(
        env=env, original=original, replacement=replacement,
        old_numeric=old_numeric, old_username=old_username,
    )


@pytest.mark.asyncio
async def test_deleted_highest_user_tokens_cannot_read_replacement_private_data_or_delete_comments(reassigned_env):
    case = reassigned_env
    env, owner = case.env, case.replacement
    application = await private_application(env, owner, "replacement")
    mine = await env.client.get(f"{APPLICATIONS}/mine", headers=owner.headers)
    assert mine.status_code == 200
    assert [item["id"] for item in mine.json()["items"]] == [application["id"]]
    assert mine.json()["items"][0]["email"] == "private-replacement@example.com"
    created = await env.client.post(
        COMMENTS, headers=owner.headers, json={"page_key": "about", "content": "仅新账户可以删除"},
    )
    assert created.status_code == 201 and created.json()["can_delete"] is True
    comment_id = created.json()["id"]

    tokens = {
        "old-integer-subject": case.old_numeric,
        "deleted-uuid-subject": case.original.token,
        "old-username-subject": case.old_username,
        "new-username-subject": create_access_token({"sub": owner.username}),
    }
    for token in tokens.values():
        await assert_private_access_denied(env, token)
        await assert_comment_readonly(env, token, comment_id)

    still_owned = await env.client.get(COMMENTS, headers=owner.headers, params={"page_key": "about"})
    assert still_owned.status_code == 200
    assert still_owned.json()["items"][0]["id"] == comment_id
    assert still_owned.json()["items"][0]["can_delete"] is True
    async with env.sessions() as db:
        comment = await db.get(Comment, comment_id)
        assert comment is not None and comment.user_id == owner.id


@pytest.mark.asyncio
async def test_refresh_frozen_uuid_cannot_adopt_reused_integer_user_id(reassigned_env):
    case = reassigned_env
    env = case.env
    # 模拟迁移遗留/损坏的刷新记录：整数外键指向新账户，冻结身份仍属于已删除账户。
    async with env.sessions() as db:
        db.add(AuthSession(
            user_id=case.replacement.id,
            auth_id=case.original.auth_id,
            token_hash=hash_token(case.original.refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        ))
        await db.commit()
        count_before = await db.scalar(select(func.count()).select_from(AuthSession))

    denied = await env.client.post(f"{AUTH}/refresh", headers=refresh_cookie(case.original.refresh_token))
    assert denied.status_code == 401
    async with env.sessions() as db:
        assert await db.scalar(select(func.count()).select_from(AuthSession)) == count_before
    legitimate = await env.client.post(
        f"{AUTH}/refresh", headers=refresh_cookie(case.replacement.refresh_token),
    )
    assert legitimate.status_code == 200
    token = legitimate.json()["access_token"]
    assert access_subject(token) == case.replacement.auth_id
    me = await env.client.get(f"{AUTH}/me", headers=bearer(token))
    assert me.status_code == 200 and me.json()["id"] == case.replacement.id


@pytest.mark.asyncio
async def test_register_login_refresh_logout_and_public_contract(auth_env):
    env = auth_env
    schemas = env.app.openapi()["components"]["schemas"]
    for name, fields in (
        ("LoginRequest", {"username", "password"}),
        ("RegisterRequest", {"username", "email", "password"}),
    ):
        assert set(schemas[name]["properties"]) == fields
        assert set(schemas[name]["required"]) == fields
        assert all(schemas[name]["properties"][field]["type"] == "string" for field in fields)

    owner = await registered(env)
    refreshed = await env.client.post(f"{AUTH}/refresh")
    assert refreshed.status_code == 200
    assert access_subject(refreshed.json()["access_token"]) == owner.auth_id
    next_refresh = env.client.cookies.get(auth_api.REFRESH_COOKIE)
    assert next_refresh and next_refresh != owner.refresh_token
    assert (await env.client.post(f"{AUTH}/refresh", headers=refresh_cookie(owner.refresh_token))).status_code == 401
    me = await env.client.get(f"{AUTH}/me", headers=bearer(refreshed.json()["access_token"]))
    assert me.status_code == 200 and me.json()["id"] == owner.id

    assert (await env.client.post(f"{AUTH}/logout", headers=refresh_cookie(next_refresh))).status_code == 204
    assert env.client.cookies.get(auth_api.REFRESH_COOKIE) is None
    assert (await env.client.post(f"{AUTH}/refresh")).status_code == 401
    assert (await env.client.post(f"{AUTH}/refresh", headers=refresh_cookie(next_refresh))).status_code == 401
    async with env.sessions() as db:
        sessions = (await db.scalars(select(AuthSession).where(AuthSession.user_id == owner.id))).all()
        assert len(sessions) == 2
        assert all(row.revoked_at is not None and row.auth_id == owner.auth_id for row in sessions)

    for identity in (owner.username, owner.email):
        login = await env.client.post(f"{AUTH}/login", json={"username": identity, "password": PASSWORD})
        assert login.status_code == 200
        token = login.json()["access_token"]
        assert access_subject(token) == owner.auth_id
        current = await env.client.get(f"{AUTH}/me", headers=bearer(token))
        assert current.status_code == 200 and current.json()["id"] == owner.id
        assert set(current.json()) == PUBLIC_USER_FIELDS
        assert (await env.client.get("/api/v1/users", headers=bearer(token))).status_code == 403
        assert (await env.client.get(f"{APPLICATIONS}/admin", headers=bearer(token))).status_code == 403
    wrong_password = await env.client.post(
        f"{AUTH}/login", json={"username": owner.username, "password": "wrong-password"},
    )
    assert wrong_password.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["expired", "revoked", "inactive", "empty-uuid", "malformed-uuid"])
async def test_refresh_rejects_unusable_sessions_without_issuing_another(auth_env, failure):
    env = auth_env
    owner = await registered(env)
    async with env.sessions() as db:
        session = await db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(owner.refresh_token)))
        assert session is not None and session.auth_id == owner.auth_id
        if failure == "expired":
            session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        elif failure == "revoked":
            session.revoked_at = datetime.now(timezone.utc)
        elif failure == "inactive":
            (await db.get(User, owner.id)).is_active = False
        elif failure == "empty-uuid":
            session.auth_id = ""
        else:
            session.auth_id = owner.auth_id.replace("-", "")
        await db.commit()

    response = await env.client.post(f"{AUTH}/refresh", headers=refresh_cookie(owner.refresh_token))
    assert response.status_code == 401
    async with env.sessions() as db:
        assert await db.scalar(select(func.count()).select_from(AuthSession)) == 1
    if failure == "inactive":
        assert (await env.client.get(f"{AUTH}/me", headers=owner.headers)).status_code == 403


@pytest.mark.asyncio
async def test_username_change_keeps_uuid_token_and_private_ownership(auth_env):
    env = auth_env
    owner = await registered(env, "original-name", "renamed@example.com")
    application = await private_application(env, owner, "rename")
    old_username_token = create_access_token({"sub": owner.username})
    async with env.sessions() as db:
        user = await db.get(User, owner.id)
        user.username = "renamed-owner"
        await db.commit()
        assert user.auth_id == owner.auth_id
    new_account = await registered(env, owner.username, "new-name-owner@example.com")

    me = await env.client.get(f"{AUTH}/me", headers=owner.headers)
    assert me.status_code == 200
    assert me.json()["id"] == owner.id and me.json()["username"] == "renamed-owner"
    mine = await env.client.get(f"{APPLICATIONS}/mine", headers=owner.headers)
    assert mine.status_code == 200 and [item["id"] for item in mine.json()["items"]] == [application["id"]]
    other_mine = await env.client.get(f"{APPLICATIONS}/mine", headers=new_account.headers)
    assert other_mine.status_code == 200 and other_mine.json() == {"items": [], "total": 0}
    await assert_private_access_denied(env, old_username_token)
    await assert_private_access_denied(env, create_access_token({"sub": "renamed-owner"}))
    login = await env.client.post(f"{AUTH}/login", json={"username": "renamed-owner", "password": PASSWORD})
    assert login.status_code == 200 and access_subject(login.json()["access_token"]) == owner.auth_id
    async with env.sessions() as db:
        assert (await db.get(User, owner.id)).auth_id == owner.auth_id


@pytest.mark.asyncio
async def test_invalid_access_credentials_never_grant_comment_permissions(auth_env):
    env = auth_env
    owner = env.users["a"]
    comment = await env.client.post(
        COMMENTS, headers=env.headers["a"], json={"page_key": "about", "content": "有效身份专属权限"},
    )
    assert comment.status_code == 201
    wrong_signature = jwt.encode(
        {"sub": owner.auth_id, "type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "a-different-signing-key", algorithm=ALGORITHM,
    )
    tokens = [
        create_access_token({"sub": owner.auth_id.upper()}),
        create_access_token({"sub": UUID(owner.auth_id).hex}),
        create_access_token({"sub": str(uuid4())}),
        create_access_token({}),
        create_access_token({"sub": owner.auth_id}, expires_delta=timedelta(seconds=-1)),
        wrong_signature,
    ]
    for token in tokens:
        await assert_private_access_denied(env, token)
        await assert_comment_readonly(env, token, comment.json()["id"])


@pytest.mark.asyncio
async def test_email_verification_and_oauth_state_cannot_act_as_access_tokens(auth_env):
    env = auth_env
    owner = env.users["a"]
    comment = await env.client.post(
        COMMENTS, headers=env.headers["a"], json={"page_key": "about", "content": "令牌用途不能提升权限"},
    )
    assert comment.status_code == 201
    authorize = await env.client.get(f"{AUTH}/github", params={"redirect": "/friends"})
    assert authorize.is_redirect
    state = parse_qs(urlsplit(authorize.headers["location"]).query)["state"][0]
    state_payload = decode_access_token(state)
    assert state_payload is not None
    assert state_payload["type"] == "oauth-state" and state_payload["sub"] == "github-oauth"

    tokens = [
        create_email_verification_token(owner.auth_id, owner.email),
        create_access_token({"sub": str(owner.id), "email": owner.email, "type": "email-verification"}),
        state,
        create_access_token({"sub": owner.auth_id, "type": "oauth-state"}),
        create_access_token({"sub": str(owner.id), "type": "oauth-state"}),
    ]
    for token in tokens:
        await assert_private_access_denied(env, token)
        await assert_comment_readonly(env, token, comment.json()["id"])


@pytest.mark.asyncio
async def test_email_verification_uses_uuid_and_rejects_legacy_or_stale_email_without_mutation(auth_env, monkeypatch):
    env = auth_env
    sent = []

    async def capture_email(email, url):
        sent.append((email, url))

    monkeypatch.setattr(auth_api, "send_verification_email", capture_email)
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION", True)
    response = await env.client.post(
        f"{AUTH}/register",
        json={"username": "verify-owner", "email": "verify@example.com", "password": PASSWORD},
    )
    assert response.status_code == 201
    assert response.json()["requires_email_verification"] is True
    assert response.json()["access_token"] is None
    assert env.client.cookies.get(auth_api.REFRESH_COOKIE) is None
    assert len(sent) == 1 and sent[0][0] == "verify@example.com"
    verification = parse_qs(urlsplit(sent[0][1]).query)["token"][0]
    payload = decode_access_token(verification)
    assert payload is not None and payload["type"] == "email-verification"
    async with env.sessions() as db:
        user = await db.scalar(select(User).where(User.username == "verify-owner"))
        user_id, auth_id = user.id, user.auth_id
        before = dict((await db.execute(select(User.__table__).where(User.id == user_id))).mappings().one())
    assert payload["sub"] == auth_id and str(UUID(auth_id)) == auth_id

    rejected = [
        create_access_token({"sub": str(user_id), "email": "verify@example.com", "type": "email-verification"}),
        create_email_verification_token(auth_id, "another@example.com"),
        create_access_token({"sub": auth_id}),
        create_access_token(
            {"sub": auth_id, "email": "verify@example.com", "type": "email-verification"},
            expires_delta=timedelta(seconds=-1),
        ),
    ]
    for token in rejected:
        confirmation = await env.client.get(f"{AUTH}/email-verification/confirm", params={"token": token})
        assert confirmation.status_code == 400
        async with env.sessions() as db:
            after = dict((await db.execute(select(User.__table__).where(User.id == user_id))).mappings().one())
            assert after == before
    blocked = await env.client.post(
        f"{AUTH}/login", json={"username": "verify-owner", "password": PASSWORD},
    )
    assert blocked.status_code == 403
    confirmed = await env.client.get(f"{AUTH}/email-verification/confirm", params={"token": verification})
    assert confirmed.status_code == 200 and confirmed.json() == {"verified": True}
    logged_in = await env.client.post(f"{AUTH}/login", json={"username": "verify-owner", "password": PASSWORD})
    assert logged_in.status_code == 200
    token = logged_in.json()["access_token"]
    assert access_subject(token) == auth_id

    async with env.sessions() as db:
        user = await db.get(User, user_id)
        user.email = "changed@example.com"
        user.email_verified = False
        await db.commit()
        changed = dict((await db.execute(select(User.__table__).where(User.id == user_id))).mappings().one())
    stale = await env.client.get(f"{AUTH}/email-verification/confirm", params={"token": verification})
    assert stale.status_code == 400
    async with env.sessions() as db:
        assert dict((await db.execute(select(User.__table__).where(User.id == user_id))).mappings().one()) == changed
    resent = await env.client.post(f"{AUTH}/email-verification/send", headers=bearer(token))
    assert resent.status_code == 204
    assert len(sent) == 2 and sent[-1][0] == "changed@example.com"
    new_verification = parse_qs(urlsplit(sent[-1][1]).query)["token"][0]
    new_payload = decode_access_token(new_verification)
    assert new_payload is not None and new_payload["sub"] == auth_id
    assert new_payload["email"] == "changed@example.com" and new_payload["type"] == "email-verification"
    assert (await env.client.get(
        f"{AUTH}/email-verification/confirm", params={"token": new_verification},
    )).status_code == 200
    async with env.sessions() as db:
        assert (await db.get(User, user_id)).email_verified is True


@pytest.mark.asyncio
@pytest.mark.parametrize("existing", [True, False], ids=["existing-oauth-user", "new-oauth-user"])
async def test_github_callback_issues_uuid_sessions_for_existing_and_new_oauth_only_users(auth_env, monkeypatch, existing):
    env = auth_env
    github_id = "1234567"
    email = "a@example.com" if existing else "new-github@example.com"
    username = "a" if existing else "new-github-owner"
    existing_uuid = env.users["a"].auth_id if existing else None
    if existing:
        async with env.sessions() as db:
            user = await db.get(User, env.users["a"].id)
            user.github_id = github_id
            assert user.password_hash == ""
            await db.commit()
    requests = []

    def github_response(request):
        requests.append((request.method, request.url.host, request.url.path))
        if request.method == "POST" and str(request.url) == "https://github.com/login/oauth/access_token":
            assert parse_qs(request.content.decode())["code"] == ["authorized-code"]
            return httpx.Response(200, json={"access_token": "github-provider-token"})
        assert request.headers["Authorization"] == "Bearer github-provider-token"
        if str(request.url) == "https://api.github.com/user":
            return httpx.Response(200, json={
                "id": int(github_id), "login": username, "name": "GitHub Owner",
                "avatar_url": "https://avatars.example.com/owner.png",
            })
        if str(request.url) == "https://api.github.com/user/emails":
            return httpx.Response(200, json=[{"email": email, "primary": True, "verified": True}])
        raise AssertionError(f"unexpected GitHub request: {request.method} {request.url}")

    monkeypatch.setattr(
        auth_api, "_github_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(github_response), trust_env=False),
    )
    authorize = await env.client.get(f"{AUTH}/github", params={"redirect": "/friends?from=oauth"})
    assert authorize.is_redirect
    location = urlsplit(authorize.headers["location"])
    assert location.hostname == "github.com"
    state = parse_qs(location.query)["state"][0]
    state_payload = decode_access_token(state)
    assert state_payload is not None
    assert state_payload["type"] == "oauth-state" and state_payload["sub"] == "github-oauth"
    await assert_private_access_denied(env, state)
    callback = await env.client.get(
        f"{AUTH}/github/callback", params={"code": "authorized-code", "state": state},
    )
    assert callback.status_code == 302
    redirected = urlsplit(callback.headers["location"])
    assert redirected.hostname == "frontend.test" and redirected.path == "/auth/callback"
    assert parse_qs(redirected.query)["redirect"] == ["/friends?from=oauth"]
    assert env.client.cookies.get(auth_api.OAUTH_STATE_COOKIE) is None
    assert requests == [
        ("POST", "github.com", "/login/oauth/access_token"),
        ("GET", "api.github.com", "/user"),
        ("GET", "api.github.com", "/user/emails"),
    ]
    async with env.sessions() as db:
        user = await db.scalar(select(User).where(User.github_id == github_id))
        assert user is not None and user.password_hash == "" and user.email_verified is True
        user_id, auth_id = user.id, user.auth_id
        assert user.email == email and user.username == username
        if existing:
            assert user_id == env.users["a"].id and auth_id == existing_uuid
        session = await db.scalar(select(AuthSession).where(AuthSession.user_id == user_id))
        assert session is not None and session.auth_id == auth_id
    refreshed = await env.client.post(f"{AUTH}/refresh")
    assert refreshed.status_code == 200
    token = refreshed.json()["access_token"]
    assert access_subject(token) == auth_id
    me = await env.client.get(f"{AUTH}/me", headers=bearer(token))
    assert me.status_code == 200 and me.json()["id"] == user_id
    assert set(me.json()) == PUBLIC_USER_FIELDS
    created = await env.client.post(
        COMMENTS, headers=bearer(token), json={"page_key": "about", "content": "OAuth 账户正常发表评论"},
    )
    assert created.status_code == 201 and created.json()["can_delete"] is True
    assert (await env.client.get("/api/v1/users", headers=bearer(token))).status_code == 403
    password_login = await env.client.post(f"{AUTH}/login", json={"username": username, "password": PASSWORD})
    assert password_login.status_code == 401


@pytest.mark.asyncio
async def test_github_callback_requires_oauth_state_even_when_cookie_matches(auth_env, monkeypatch):
    env = auth_env
    owner = env.users["a"]

    def unexpected_github_request(request):
        raise AssertionError("OAuth state 的用途应在访问 GitHub 前被拒绝")

    monkeypatch.setattr(
        auth_api, "_github_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(unexpected_github_request), trust_env=False),
    )
    for token_type in ("access", "email-verification"):
        token = create_access_token({"sub": owner.auth_id, "email": owner.email, "type": token_type})
        response = await env.client.get(
            f"{AUTH}/github/callback",
            params={"code": "authorized-code", "state": token},
            headers={"Cookie": f"{auth_api.OAUTH_STATE_COOKIE}={hash_token(token)}"},
        )
        assert response.status_code == 400
    async with env.sessions() as db:
        assert await db.scalar(select(func.count()).select_from(AuthSession)) == 0


def mock_github(monkeypatch, github_id, email):
    """仅替换外部 GitHub，保留真实回调、数据库与会话。"""
    def github_response(request):
        if request.url.host == "github.com":
            return httpx.Response(200, json={"access_token": "provider-token"})
        if request.url.path == "/user":
            return httpx.Response(200, json={"id": int(github_id), "login": "github-owner", "avatar_url": "https://avatars.example.com/link.png"})
        if request.url.path == "/user/emails":
            return httpx.Response(200, json=[{"email": email, "primary": True, "verified": True}])
        raise AssertionError(f"unexpected GitHub request: {request.url}")

    monkeypatch.setattr(auth_api, "_github_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(github_response)))


async def github_callback(env, redirect="/friends?from=link"):
    authorize = await env.client.get(f"{AUTH}/github", params={"redirect": redirect})
    state = parse_qs(urlsplit(authorize.headers["location"]).query)["state"][0]
    assert decode_access_token(state)["nonce"]
    return await env.client.get(f"{AUTH}/github/callback", params={"code": "authorized-code", "state": state})


@pytest.mark.asyncio
async def test_github_email_match_requires_password_confirmation(auth_env, monkeypatch):
    env = auth_env
    owner = await registered(env)
    env.client.cookies.clear()
    mock_github(monkeypatch, "987654321", owner.email)
    async with env.sessions() as db:
        before = await db.scalar(select(func.count()).select_from(AuthSession))
    callback = await github_callback(env)
    location = urlsplit(callback.headers["location"])
    assert callback.status_code == 302 and location.path == "/auth/link-github"
    query = parse_qs(location.query)
    assert query["redirect"] == ["/friends?from=link"]
    link_token = query["token"][0]
    assert env.client.cookies.get(auth_api.REFRESH_COOKIE) is None
    assert env.client.cookies.get(auth_api.OAUTH_STATE_COOKIE) is None
    async with env.sessions() as db:
        assert not (await db.get(User, owner.id)).github_id
        assert await db.scalar(select(func.count()).select_from(AuthSession)) == before
    await assert_private_access_denied(env, link_token)
    wrong = await env.client.post(f"{AUTH}/github/confirm-link", json={"link_token": link_token, "password": "wrong-password"})
    assert wrong.status_code == 401 and wrong.json()["detail"] == "密码错误"
    assert env.client.cookies.get(auth_api.REFRESH_COOKIE) is None
    confirmed = await env.client.post(f"{AUTH}/github/confirm-link", json={"link_token": link_token, "password": PASSWORD})
    assert confirmed.status_code == 200
    assert access_subject(confirmed.json()["access_token"]) == owner.auth_id
    me = await env.client.get(f"{AUTH}/me", headers=bearer(confirmed.json()["access_token"]))
    assert me.status_code == 200 and me.json()["id"] == owner.id
    async with env.sessions() as db:
        user = await db.get(User, owner.id)
        assert user.github_id == "987654321" and user.email_verified
        assert user.avatar_url == "https://avatars.example.com/link.png"
    password_login = await env.client.post(f"{AUTH}/login", json={"username": owner.email, "password": PASSWORD})
    assert password_login.status_code == 200
    me = await env.client.get(f"{AUTH}/me", headers=bearer(password_login.json()["access_token"]))
    assert me.json()["id"] == owner.id
    env.client.cookies.clear()
    second = await github_callback(env)
    assert urlsplit(second.headers["location"]).path == "/auth/callback"
    assert env.client.cookies.get(auth_api.REFRESH_COOKIE)


@pytest.mark.asyncio
async def test_github_link_token_cannot_be_reused_or_cross_bound(auth_env, monkeypatch):
    env = auth_env
    owner = await registered(env)
    mock_github(monkeypatch, "987654322", owner.email)
    callback = await github_callback(env)
    token = parse_qs(urlsplit(callback.headers["location"]).query)["token"][0]
    async with env.sessions() as db:
        other = await db.get(User, env.users["b"].id)
        other.github_id = "987654322"
        await db.commit()
    conflict = await env.client.post(f"{AUTH}/github/confirm-link", json={"link_token": token, "password": PASSWORD})
    assert conflict.status_code == 409 and conflict.json()["detail"] == "该 GitHub 账户已被绑定"
    async with env.sessions() as db:
        assert not (await db.get(User, owner.id)).github_id
        other = await db.get(User, env.users["b"].id)
        other.github_id = None
        await db.commit()
    success = await env.client.post(f"{AUTH}/github/confirm-link", json={"link_token": token, "password": PASSWORD})
    assert success.status_code == 200
    replay = await env.client.post(f"{AUTH}/github/confirm-link", json={"link_token": token, "password": PASSWORD})
    assert replay.status_code == 409 and replay.json()["detail"] == "该账户已绑定 GitHub"


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["expired", "access", "invalid-subject", "missing-github", "disabled", "deleted", "changed-email"])
async def test_github_link_rejects_invalid_claims_and_stale_accounts(auth_env, case):
    env = auth_env
    owner = await registered(env)
    claims = {"sub": owner.auth_id, "type": "github-link", "github_id": "987654323", "github_email": owner.email}
    if case == "access":
        claims["type"] = "access"
    elif case == "invalid-subject":
        claims["sub"] = str(owner.id)
    elif case == "missing-github":
        claims.pop("github_id")
    async with env.sessions() as db:
        user = await db.get(User, owner.id)
        user.email_verified = False
        if case == "disabled":
            user.is_active = False
        elif case == "deleted":
            await db.delete(user)
        elif case == "changed-email":
            user.email = "changed@example.com"
        await db.commit()
    token = create_access_token(claims, expires_delta=timedelta(seconds=-1) if case == "expired" else timedelta(minutes=10))
    response = await env.client.post(f"{AUTH}/github/confirm-link", json={"link_token": token, "password": PASSWORD})
    assert response.status_code == (200 if case == "changed-email" else 401)
    async with env.sessions() as db:
        user = await db.get(User, owner.id)
        if case == "changed-email":
            assert user.github_id == "987654323" and not user.email_verified
        elif user:
            assert not user.github_id


@pytest.mark.asyncio
async def test_github_concurrent_link_confirmation_has_one_winner(auth_env):
    import asyncio

    env = auth_env
    owner = await registered(env)
    token = create_access_token({"sub": owner.auth_id, "type": "github-link", "github_id": "987654324"})
    async with env.sessions() as db:
        before = await db.scalar(select(func.count()).select_from(AuthSession))
    responses = await asyncio.gather(*[
        env.client.post(f"{AUTH}/github/confirm-link", json={"link_token": token, "password": PASSWORD}) for _ in range(2)
    ])
    assert sorted(response.status_code for response in responses) == [200, 409]
    async with env.sessions() as db:
        assert (await db.get(User, owner.id)).github_id == "987654324"
        assert await db.scalar(select(func.count()).select_from(AuthSession)) == before + 1

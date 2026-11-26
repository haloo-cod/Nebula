"""多域名入口必须先到回调主机，再写入 host-only OAuth state Cookie。"""

from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from sqlalchemy import func, select

from app.api.v1 import auth as auth_api
from app.config import settings
from app.models.user import User
from tests.test_auth_identity import auth_env, mock_github  # noqa: F401
from tests.test_friend_snapshot import friend_env  # noqa: F401

PATH = "/api/v1/auth/github"


@pytest.mark.asyncio
@pytest.mark.parametrize("canonical,alias", [
    ("starlitn.top", "blog.starlitn.top"),
    ("blog.starlitn.top", "starlitn.top"),
])
async def test_alias_redirects_before_state_cookie_and_completes_login(auth_env, monkeypatch, canonical, alias):
    """真实 CookieJar、回调和数据库，只模拟外部 GitHub API。"""
    env = auth_env
    callback = f"https://{canonical}{PATH}/callback"
    monkeypatch.setattr(settings, "GITHUB_CALLBACK_URL", callback)
    monkeypatch.setattr(settings, "FRONTEND_URL", f"https://{canonical}")
    monkeypatch.setattr(settings, "COOKIE_SECURE", True)
    mock_github(monkeypatch, "987651234", "domain-login@example.com")
    async with env.sessions() as db:
        before = await db.scalar(select(func.count()).select_from(User))

    entry = await env.client.get(f"https://{alias}{PATH}", params={"redirect": "/friends?from=github#exchange"})
    assert entry.status_code == 307
    assert entry.headers["cache-control"] == "no-store"
    assert "set-cookie" not in entry.headers
    canonical_url = urlsplit(entry.headers["location"])
    assert canonical_url.scheme == "https" and canonical_url.netloc == canonical
    assert canonical_url.path == PATH
    assert parse_qs(canonical_url.query) == {"redirect": ["/friends?from=github#exchange"]}

    authorize = await env.client.get(entry.headers["location"])
    assert authorize.status_code == 307 and authorize.headers["cache-control"] == "no-store"
    github = urlsplit(authorize.headers["location"])
    assert github.netloc == "github.com" and github.path == "/login/oauth/authorize"
    query = parse_qs(github.query)
    assert query["redirect_uri"] == [callback]
    cookie = authorize.headers["set-cookie"].lower()
    assert "httponly" in cookie and "secure" in cookie and "samesite=lax" in cookie
    assert "domain=" not in cookie
    assert f"path={PATH}/callback" in cookie
    complete = await env.client.get(callback, params={"code": "test-authorized-code", "state": query["state"][0]})
    assert complete.status_code == 302
    destination = urlsplit(complete.headers["location"])
    assert destination.netloc == canonical and destination.path == "/auth/callback"
    assert parse_qs(destination.query) == {"redirect": ["/friends?from=github#exchange"]}
    assert auth_api.OAUTH_STATE_COOKIE not in env.client.cookies
    refreshed = await env.client.post(f"https://{canonical}/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    me = await env.client.get(f"https://{canonical}/api/v1/auth/me", headers={"Authorization": f"Bearer {refreshed.json()['access_token']}"})
    assert me.status_code == 200 and me.json()["email"] == "domain-login@example.com"
    async with env.sessions() as db:
        assert await db.scalar(select(func.count()).select_from(User)) == before + 1
        assert await db.scalar(select(User.id).where(User.github_id == "987651234")) == me.json()["id"]


@pytest.mark.asyncio
async def test_cloudflare_http_origin_has_no_self_redirect_loop(auth_env, monkeypatch):
    """外部 HTTPS、源站 HTTP 时，不能仅因协议不同而重复跳回自己。"""
    monkeypatch.setattr(settings, "GITHUB_CALLBACK_URL", "https://starlitn.top/api/v1/auth/github/callback")
    monkeypatch.setattr(settings, "COOKIE_SECURE", True)
    result = await auth_env.client.get(f"http://starlitn.top{PATH}")
    assert result.status_code == 307 and urlsplit(result.headers["location"]).hostname == "github.com"
    assert "secure" in result.headers["set-cookie"].lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("redirect", ["//outside.example/path", "https://outside.example/path"])
async def test_alias_cannot_choose_redirect_host_or_external_return(auth_env, monkeypatch, redirect):
    """忽略客户端提交的代理主机，以配置为唯一跳转目标。"""
    monkeypatch.setattr(settings, "GITHUB_CALLBACK_URL", "https://starlitn.top/api/v1/auth/github/callback")
    result = await auth_env.client.get(
        f"https://blog.starlitn.top{PATH}", params={"redirect": redirect},
        headers={"X-Forwarded-Host": "outside.example", "X-Forwarded-Proto": "http"},
    )
    location = urlsplit(result.headers["location"])
    assert location.netloc == "starlitn.top" and parse_qs(location.query) == {"redirect": ["/"]}
    assert "set-cookie" not in result.headers


@pytest.mark.asyncio
async def test_missing_state_cookie_is_still_rejected_without_creating_user(auth_env, monkeypatch):
    """修复别名入口不会削弱回调的 Cookie 绑定检查。"""
    monkeypatch.setattr(settings, "GITHUB_CALLBACK_URL", "https://starlitn.top/api/v1/auth/github/callback")
    authorize = await auth_env.client.get(f"https://starlitn.top{PATH}")
    state = parse_qs(urlsplit(authorize.headers["location"]).query)["state"][0]
    auth_env.client.cookies.clear()

    def forbidden(request):
        raise AssertionError("缺少 Cookie 时不应向 GitHub 换取 token")

    monkeypatch.setattr(auth_api, "_github_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(forbidden)))
    async with auth_env.sessions() as db:
        before = await db.scalar(select(func.count()).select_from(User))
    denied = await auth_env.client.get(f"https://starlitn.top{PATH}/callback", params={"code": "test-code", "state": state})
    assert denied.status_code == 400 and denied.json()["detail"] == "OAuth state 无效"
    async with auth_env.sessions() as db:
        assert await db.scalar(select(func.count()).select_from(User)) == before


@pytest.mark.asyncio
@pytest.mark.parametrize("callback", ["/callback", "ftp://example.com/callback", "https://user:pass@example.com/callback", "https://example.com:bad/callback"])
async def test_invalid_callback_is_configuration_error(auth_env, monkeypatch, callback):
    monkeypatch.setattr(settings, "GITHUB_CALLBACK_URL", callback)
    result = await auth_env.client.get(f"https://blog.starlitn.top{PATH}")
    assert result.status_code == 503 and result.json()["detail"] == "GitHub 回调地址配置无效"
    assert "set-cookie" not in result.headers

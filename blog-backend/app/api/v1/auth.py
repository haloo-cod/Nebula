"""统一账户认证：密码注册登录、刷新会话与 GitHub OAuth。"""

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.user import AuthSession, User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.email import send_verification_email
from app.utils.security import (
    create_access_token,
    create_email_verification_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["认证"])
REFRESH_COOKIE = "blog_refresh_token"
OAUTH_STATE_COOKIE = "blog_oauth_state"


def _safe_redirect(value: str | None) -> str:
    """仅允许站内绝对路径作为 OAuth 完成后的跳转地址。"""
    if not value or not value.startswith("/") or value.startswith("//"):
        return "/"
    return value[:500]


def _github_client() -> httpx.AsyncClient:
    """创建 GitHub HTTP 客户端，支持显式 HTTP 代理和环境代理。"""

    kwargs: dict[str, object] = {
        "timeout": httpx.Timeout(settings.GITHUB_HTTP_TIMEOUT),
        "follow_redirects": False,
        "trust_env": True,
    }
    if settings.GITHUB_HTTP_PROXY:
        kwargs["proxy"] = settings.GITHUB_HTTP_PROXY
    return httpx.AsyncClient(**kwargs)


def _set_refresh_cookie(response: Response, token: str) -> None:
    """写入只允许认证接口使用的 HttpOnly 刷新 Cookie。"""

    response.set_cookie(
        REFRESH_COOKIE,
        token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/api/v1/auth",
    )


async def _create_session(user: User, db: AsyncSession, response: Response) -> TokenResponse:
    """创建刷新会话并返回短期访问令牌。"""

    refresh_token = create_refresh_token()
    db.add(
        AuthSession(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=create_access_token({"sub": str(user.id)}))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """创建普通用户并立即登录。"""

    result = await db.execute(
        select(User).where(or_(User.username == body.username, User.email == body.email))
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名或邮箱已被使用")
    user = User(
        username=body.username,
        email=body.email,
        display_name=body.username,
        password_hash=hash_password(body.password),
        email_verified=not settings.REQUIRE_EMAIL_VERIFICATION,
    )
    db.add(user)
    await db.flush()
    if settings.REQUIRE_EMAIL_VERIFICATION:
        verification_token = create_email_verification_token(user.id, body.email)
        verification_url = f"{settings.FRONTEND_URL}/#/verify-email?token={verification_token}"
        await send_verification_email(body.email, verification_url)
    return await _create_session(user, db, response)


@router.post("/email-verification/send", status_code=status.HTTP_204_NO_CONTENT)
async def resend_email_verification(
    user: User = Depends(get_current_user),
):
    """为当前未验证账户重新发送验证链接。"""

    if user.email_verified or not user.email:
        return
    token = create_email_verification_token(user.id, user.email)
    await send_verification_email(user.email, f"{settings.FRONTEND_URL}/#/verify-email?token={token}")


@router.get("/email-verification/confirm")
async def confirm_email_verification(token: str, db: AsyncSession = Depends(get_db)):
    """校验验证令牌并激活当前邮箱。"""

    payload = decode_access_token(token)
    if not payload or payload.get("type") != "email-verification":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱验证链接无效或已过期")
    user = await db.get(User, int(payload["sub"]))
    if not user or user.email != payload.get("email"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱验证链接已失效")
    user.email_verified = True
    await db.commit()
    return {"verified": True}


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """使用用户名或邮箱登录。"""

    identity = body.username.strip()
    result = await db.execute(
        select(User).where(or_(User.username == identity, User.email == identity.lower()))
    )
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名、邮箱或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已被禁用")
    return await _create_session(user, db, response)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_session(
    response: Response,
    refresh_token: str | None = Cookie(None, alias=REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    """轮换刷新令牌并签发新的访问令牌。"""

    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录会话不存在")
    result = await db.execute(
        select(AuthSession).where(AuthSession.token_hash == hash_token(refresh_token))
    )
    session = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if not session or session.revoked_at or session.expires_at.replace(tzinfo=timezone.utc) <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录会话已失效")
    user = await db.get(User, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账户不可用")
    session.revoked_at = now
    return await _create_session(user, db, response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(None, alias=REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    """撤销当前刷新会话。"""

    if refresh_token:
        result = await db.execute(
            select(AuthSession).where(AuthSession.token_hash == hash_token(refresh_token))
        )
        session = result.scalar_one_or_none()
        if session and not session.revoked_at:
            session.revoked_at = datetime.now(timezone.utc)
            await db.commit()
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")


@router.get("/github")
async def github_login(redirect: str | None = Query(None, max_length=500)):
    """跳转至 GitHub OAuth 授权页面。"""

    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GitHub 登录未配置")
    state_token = create_access_token(
        {
            "sub": "github-oauth",
            "type": "oauth-state",
            "redirect": _safe_redirect(redirect),
        },
        expires_delta=timedelta(minutes=10),
    )
    query = urlencode({
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_CALLBACK_URL,
        "scope": "read:user user:email",
        "state": state_token,
    })
    response = RedirectResponse(f"https://github.com/login/oauth/authorize?{query}")
    response.set_cookie(
        OAUTH_STATE_COOKIE,
        hash_token(state_token),
        max_age=600,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/api/v1/auth/github/callback",
    )
    return response


@router.get("/github/callback")
async def github_callback(
    code: str,
    state: str,
    oauth_state: str | None = Cookie(None, alias=OAUTH_STATE_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    """处理 GitHub 回调，创建或登录统一账户。"""

    state_payload = decode_access_token(state)
    if (
        not state_payload
        or state_payload.get("type") != "oauth-state"
        or not oauth_state
        or oauth_state != hash_token(state)
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth state 无效")
    try:
        async with _github_client() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_CALLBACK_URL,
                },
            )
            if token_response.status_code != status.HTTP_200_OK:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="GitHub 授权服务返回异常，请稍后重试",
                )
            github_token = token_response.json().get("access_token")
            if not github_token:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub 授权失败")
            headers = {
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
            }
            profile_response = await client.get("https://api.github.com/user", headers=headers)
            emails_response = await client.get("https://api.github.com/user/emails", headers=headers)
            if profile_response.status_code != status.HTTP_200_OK or emails_response.status_code != status.HTTP_200_OK:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="无法从 GitHub 读取用户资料，请稍后重试",
                )
            profile = profile_response.json()
            emails = emails_response.json()
    except HTTPException:
        raise
    except httpx.TimeoutException as exc:
        print(f"[auth] GitHub OAuth 请求超时: {exc.__class__.__name__}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="后端连接 GitHub 超时，请检查网络或 GITHUB_HTTP_PROXY 配置",
        ) from exc
    except httpx.RequestError as exc:
        print(f"[auth] GitHub OAuth 网络请求失败: {exc.__class__.__name__}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="后端无法连接 GitHub，请检查网络或 GITHUB_HTTP_PROXY 配置",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub 返回了无法解析的响应",
        ) from exc
    github_id = str(profile.get("id", ""))
    if not github_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无法读取 GitHub 用户资料")
    email = next((item["email"].lower() for item in emails if item.get("primary") and item.get("verified")), None)
    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()
    if not user and email:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if not user:
        base = "".join(char for char in str(profile.get("login", "github-user")) if char.isalnum() or char in "_-")[:24] or "github-user"
        username = base
        suffix = 1
        while (await db.execute(select(User.id).where(User.username == username))).scalar_one_or_none():
            suffix += 1
            username = f"{base}-{suffix}"
        user = User(username=username, password_hash="", email=email, display_name=profile.get("name") or username, avatar_url=profile.get("avatar_url") or "", github_id=github_id, email_verified=bool(email))
        db.add(user)
        await db.flush()
    elif not user.github_id:
        user.github_id = github_id
        user.avatar_url = user.avatar_url or profile.get("avatar_url") or ""
        user.email_verified = user.email_verified or bool(email)
    redirect_path = _safe_redirect(state_payload.get("redirect"))
    redirect = RedirectResponse(
        f"{settings.FRONTEND_URL}/#/auth/callback?redirect={urlencode({'': redirect_path})[1:]}",
        status_code=status.HTTP_302_FOUND,
    )
    redirect.delete_cookie(OAUTH_STATE_COOKIE, path="/api/v1/auth/github/callback")
    await _create_session(user, db, redirect)
    return redirect


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """获取当前登录用户信息。"""

    return user

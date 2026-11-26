"""友链申请的权限、状态机、公开/私有视图、评论与 JSON 快照集成回归。"""

import asyncio
import json

import pytest
from sqlalchemy import func, select
from fastapi import HTTPException

from app.models.comment import Comment
from app.models.friend import Friend
from app.models.friend_application import FriendApplication
from app.models.user import User
from app.schemas.friend import FriendApplicationCreate
from app.services import friend as friend_service
from app.services.friend_application import create_application, delete_application
from tests.test_friend_snapshot import friend_env  # noqa: F401

APPLICATIONS = "/api/v1/friends/applications"
COMMENTS = "/api/v1/comments"

PUBLIC_FIELDS = {"id", "name", "url", "avatar", "rss_url", "created_at", "reviewed_at", "friend_id"}
PRIVATE_FIELDS = PUBLIC_FIELDS | {"email", "user_id", "status", "review_note"}


def application_payload(**overrides):
    """合法的申请请求；按需覆盖或删减字段。"""
    data = {
        "name": "测试站",
        "url": "https://example.com/",
        "avatar": "https://example.com/avatar.png",
        "email": "owner@example.com",
        "rss_url": "",
    }
    data.update(overrides)
    return data


async def submit_with(env, headers, **overrides):
    return await env.client.post(APPLICATIONS, headers=headers, json=application_payload(**overrides))


async def approve(env, application_id, headers=None):
    return await env.client.patch(
        f"{APPLICATIONS}/{application_id}/review",
        headers=headers if headers is not None else env.headers["admin"],
        json={"decision": "approved"},
    )


async def reject(env, application_id, reason=None, headers=None):
    body = {"decision": "rejected"}
    if reason is not None:
        body["reason"] = reason
    return await env.client.patch(
        f"{APPLICATIONS}/{application_id}/review",
        headers=headers if headers is not None else env.headers["admin"],
        json=body,
    )


async def row_count(env, model, *conditions):
    statement = select(func.count()).select_from(model)
    if conditions:
        statement = statement.where(*conditions)
    async with env.sessions() as db:
        return int(await db.scalar(statement) or 0)


async def scalar_value(env, statement):
    async with env.sessions() as db:
        return await db.scalar(statement)


def snapshot(env):
    return json.loads(env.path.read_text("utf-8"))


def assert_public_shape(item):
    assert set(item) == PUBLIC_FIELDS
    assert isinstance(item["friend_id"], int)
    assert item["reviewed_at"]


def assert_private_shape(item):
    assert set(item) == PRIVATE_FIELDS


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("remove_fields", "overrides"),
    [
        pytest.param({"name"}, {}, id="missing-name"),
        pytest.param({"url"}, {}, id="missing-url"),
        pytest.param({"avatar"}, {}, id="missing-avatar"),
        pytest.param({"email"}, {}, id="missing-email"),
        pytest.param(set(), {"name": "   "}, id="blank-name"),
        pytest.param(set(), {"name": "x" * 101}, id="long-name"),
        pytest.param(set(), {"email": "not-an-email"}, id="invalid-email"),
        pytest.param(set(), {"url": "javascript:alert(1)"}, id="javascript-site"),
        pytest.param(set(), {"url": "/relative"}, id="relative-site"),
        pytest.param(set(), {"url": "https://user:pass@example.com/"}, id="credential-site"),
        pytest.param(set(), {"avatar": "javascript:alert(1)"}, id="javascript-avatar"),
        pytest.param(set(), {"avatar": "https://example.com/a b.png"}, id="space-avatar"),
        pytest.param(set(), {"rss_url": "ftp://example.com/rss.xml"}, id="invalid-rss"),
        pytest.param(set(), {"rss_url": "not-a-url"}, id="relative-rss"),
        pytest.param(set(), {"status": "approved"}, id="server-owned-status"),
    ],
)
async def test_invalid_application_inputs_are_rejected(friend_env, remove_fields, overrides):
    """必填、格式、协议、凭据、RSS 和服务器字段全部由请求契约拦住。"""
    env = friend_env
    body = application_payload(**overrides)
    for field in remove_fields:
        body.pop(field)

    response = await env.client.post(APPLICATIONS, headers=env.headers["a"], json=body)

    assert response.status_code == 422
    assert await row_count(env, FriendApplication) == 0


@pytest.mark.asyncio
async def test_permissions_private_visibility_and_duplicate_site_keys(friend_env):
    """匿名/禁用/普通用户边界，公开列表不含待审记录或邮箱。"""
    env = friend_env
    client = env.client

    assert (await client.post(APPLICATIONS, json=application_payload())).status_code == 401
    assert (
        await client.post(APPLICATIONS, headers=env.headers["disabled"], json=application_payload())
    ).status_code == 403

    body = {
        "name": "第一站",
        "url": "https://one.example.com/",
        "avatar": "https://one.example.com/avatar.png",
        "email": "owner@example.com",
    }
    created = await client.post(APPLICATIONS, headers=env.headers["a"], json=body)
    assert created.status_code == 201
    application = created.json()
    assert_private_shape(application)
    assert application["status"] == "pending"
    assert application["friend_id"] is None
    assert application["reviewed_at"] is None
    assert application["review_note"] == ""
    assert application["rss_url"] == ""
    assert application["email"] == "owner@example.com"
    assert application["user_id"] == 1
    application_id = application["id"]

    duplicate = await submit_with(env, env.headers["a"], url="https://one.example.com/#section")
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "该站点已有待审核或已通过的申请"
    duplicate_no_slash = await submit_with(env, env.headers["a"], url="https://one.example.com")
    assert duplicate_no_slash.status_code == 409
    duplicate_by_b = await submit_with(env, env.headers["b"], url="https://one.example.com/")
    assert duplicate_by_b.status_code == 409
    assert await row_count(env, FriendApplication) == 1

    # query 与路径大小写属于不同站点，应允许申请。
    with_query = await submit_with(env, env.headers["a"], url="https://one.example.com/?ref=1")
    assert with_query.status_code == 201

    b_only = await submit_with(env, env.headers["b"], url="https://b.example.com/")
    assert b_only.status_code == 201
    assert await row_count(env, FriendApplication) == 3

    # 普通用户不能审核、删除或重建 JSON；匿名访问受保护读接口是 401。
    pending_id = with_query.json()["id"]
    assert (await client.get(f"{APPLICATIONS}/admin", headers=env.headers["a"])).status_code == 403
    assert (await client.get(f"{APPLICATIONS}/admin")).status_code == 401
    assert (await client.get(f"{APPLICATIONS}/mine")).status_code == 401
    assert (await client.patch(
        f"{APPLICATIONS}/{pending_id}/review", headers=env.headers["a"], json={"decision": "approved"}
    )).status_code == 403
    assert (await client.patch(
        f"{APPLICATIONS}/{pending_id}/review", json={"decision": "approved"}
    )).status_code == 401
    assert (await client.delete(f"{APPLICATIONS}/{pending_id}", headers=env.headers["a"])).status_code == 403
    assert (await client.delete(f"{APPLICATIONS}/{pending_id}")).status_code == 401
    assert (await client.post("/api/v1/friends/sync-json", headers=env.headers["a"])).status_code == 403
    assert (await client.post("/api/v1/friends/sync-json")).status_code == 401

    public = await client.get(APPLICATIONS)
    assert public.status_code == 200
    assert public.json() == {"items": [], "total": 0}
    assert "owner@example.com" not in public.text
    assert (await client.get("/api/v1/friends")).json()["total"] == 0

    mine_a = (await client.get(f"{APPLICATIONS}/mine", headers=env.headers["a"])).json()
    assert mine_a["total"] == 2
    assert {item["id"] for item in mine_a["items"]} == {application_id, pending_id}
    assert all(item["email"] == "owner@example.com" for item in mine_a["items"])
    assert all(set(item) == PRIVATE_FIELDS for item in mine_a["items"])

    mine_b = (await client.get(f"{APPLICATIONS}/mine", headers=env.headers["b"])).json()
    assert mine_b["total"] == 1
    assert {item["id"] for item in mine_b["items"]} == {b_only.json()["id"]}
    assert application_id not in {item["id"] for item in mine_b["items"]}

    admin_list = (await client.get(f"{APPLICATIONS}/admin", headers=env.headers["admin"])).json()
    assert admin_list["total"] == 3
    assert "owner@example.com" in json.dumps(admin_list, ensure_ascii=False)
    assert {item["id"] for item in admin_list["items"]} == {application_id, pending_id, b_only.json()["id"]}

    filtered_approved = (await client.get(
        f"{APPLICATIONS}/admin", headers=env.headers["admin"], params={"status": "approved"}
    )).json()
    assert filtered_approved["total"] == 0
    filtered_pending = (await client.get(
        f"{APPLICATIONS}/admin", headers=env.headers["admin"], params={"status": "pending"}
    )).json()
    assert filtered_pending["total"] == 3
    assert (await client.get(
        f"{APPLICATIONS}/admin", headers=env.headers["admin"], params={"status": "rejected"}
    )).json()["total"] == 0


@pytest.mark.asyncio
async def test_pagination_totals_and_scopes(friend_env):
    """公开、本人和管理端分页 total 使用各自过滤条件且页间不重复。"""
    env = friend_env
    client = env.client

    async def create(headers, name):
        response = await submit_with(env, headers, name=name, url=f"https://{name}.example.com/")
        assert response.status_code == 201
        return response.json()["id"]

    a1 = await create(env.headers["a"], "a1")
    a2 = await create(env.headers["a"], "a2")
    a3 = await create(env.headers["a"], "a3")
    b1 = await create(env.headers["b"], "b1")
    b2 = await create(env.headers["b"], "b2")

    assert (await approve(env, a1)).status_code == 200
    assert (await approve(env, a2)).status_code == 200
    assert (await approve(env, b1)).status_code == 200
    rejected = await reject(env, b2, "内容不足")
    assert rejected.status_code == 200

    public_total = (await client.get(APPLICATIONS)).json()["total"]
    assert public_total == 3
    public_one = (await client.get(APPLICATIONS, params={"page": 1, "page_size": 2})).json()
    public_two = (await client.get(APPLICATIONS, params={"page": 2, "page_size": 2})).json()
    assert public_one["total"] == public_two["total"] == 3
    assert [len(public_one["items"]), len(public_two["items"])] == [2, 1]
    public_items = public_one["items"] + public_two["items"]
    assert {item["id"] for item in public_items} == {a1, a2, b1}
    assert all(set(item) == PUBLIC_FIELDS for item in public_items)
    order_keys = [(item["reviewed_at"], item["id"]) for item in public_items]
    assert order_keys == sorted(order_keys, key=lambda pair: (pair[0], pair[1]), reverse=True)
    assert (await client.get(APPLICATIONS, params={"page_size": 51})).status_code == 422

    mine_a_one = (await client.get(
        f"{APPLICATIONS}/mine", headers=env.headers["a"], params={"page": 1, "page_size": 2}
    )).json()
    mine_a_two = (await client.get(
        f"{APPLICATIONS}/mine", headers=env.headers["a"], params={"page": 2, "page_size": 2}
    )).json()
    assert mine_a_one["total"] == mine_a_two["total"] == 3
    assert [len(mine_a_one["items"]), len(mine_a_two["items"])] == [2, 1]
    mine_a_items = mine_a_one["items"] + mine_a_two["items"]
    assert {item["id"] for item in mine_a_items} == {a1, a2, a3}
    assert all(set(item) == PRIVATE_FIELDS for item in mine_a_items)
    mine_keys = [(item["created_at"], item["id"]) for item in mine_a_items]
    assert mine_keys == sorted(mine_keys, key=lambda pair: (pair[0], pair[1]), reverse=True)
    assert (await client.get(
        f"{APPLICATIONS}/mine", headers=env.headers["a"], params={"page_size": 0}
    )).status_code == 422

    mine_b = (await client.get(f"{APPLICATIONS}/mine", headers=env.headers["b"])).json()
    assert mine_b["total"] == 2 and {item["id"] for item in mine_b["items"]} == {b1, b2}

    admin_all = (await client.get(
        f"{APPLICATIONS}/admin", headers=env.headers["admin"], params={"page": 1, "page_size": 2}
    )).json()
    assert admin_all["total"] == 5
    admin_approved = (await client.get(
        f"{APPLICATIONS}/admin", headers=env.headers["admin"], params={"status": "approved"}
    )).json()
    assert admin_approved["total"] == 3
    assert {item["id"] for item in admin_approved["items"]} == {a1, a2, b1}
    admin_rejected = (await client.get(
        f"{APPLICATIONS}/admin", headers=env.headers["admin"], params={"status": "rejected"}
    )).json()
    assert admin_rejected["total"] == 1 and admin_rejected["items"][0]["id"] == b2
    assert admin_rejected["items"][0]["review_note"] == "内容不足"
    admin_pending = (await client.get(
        f"{APPLICATIONS}/admin", headers=env.headers["admin"], params={"status": "pending"}
    )).json()
    assert admin_pending["total"] == 1 and admin_pending["items"][0]["id"] == a3


@pytest.mark.asyncio
async def test_formal_friend_collision_and_legacy_url_are_handled(friend_env):
    """正式友链站点（含片段归一化）阻止申请；无法解析的旧地址不会挡路。"""
    env = friend_env
    client = env.client

    manual = await client.post(
        "/api/v1/friends",
        headers=env.headers["admin"],
        json={"name": "已有站点", "url": "https://taken.example.com/site#top"},
    )
    assert manual.status_code == 201
    collision = await submit_with(env, env.headers["a"], url="https://taken.example.com/site")
    assert collision.status_code == 409
    assert collision.json()["detail"] == "该站点已在友链中"

    distinct_query = await submit_with(env, env.headers["a"], url="https://taken.example.com/site?ref=1")
    assert distinct_query.status_code == 201

    legacy = await client.post(
        "/api/v1/friends",
        headers=env.headers["admin"],
        json={"name": "旧站", "url": "legacy-address"},
    )
    assert legacy.status_code == 201
    fresh = await submit_with(env, env.headers["b"], url="https://fresh.example.com/")
    assert fresh.status_code == 201
    assert await row_count(env, FriendApplication) == 2

    data = snapshot(env)
    assert len(data) == 2
    assert "owner@example.com" not in env.path.read_text("utf-8")

    late = await submit_with(env, env.headers["a"], name="后补友链", url="https://late.example.com/")
    assert late.status_code == 201
    late_id = late.json()["id"]
    assert (await client.post(
        "/api/v1/friends",
        headers=env.headers["admin"],
        json={"name": "后来手工添加", "url": "https://late.example.com/"},
    )).status_code == 201
    approval_collision = await approve(env, late_id)
    assert approval_collision.status_code == 409
    assert approval_collision.json()["detail"] == "该站点已在友链中"
    assert await scalar_value(
        env, select(FriendApplication.status).where(FriendApplication.id == late_id)
    ) == "pending"
    assert await row_count(env, Friend, Friend.url == "https://late.example.com/") == 1
    assert (await client.get(APPLICATIONS)).json()["total"] == 0


@pytest.mark.asyncio
async def test_approval_creates_one_friend_and_snapshot_idempotently(friend_env):
    """批准链路一次生成正式友链、公开申请和 JSON；重复批准只返回同一条记录。"""
    env = friend_env
    client = env.client

    assert (await approve(env, 9999)).status_code == 404

    created = await submit_with(
        env,
        env.headers["a"],
        name="申请站",
        url="https://approved.example.com/",
        avatar="https://approved.example.com/avatar.png",
        rss_url="https://approved.example.com/rss.xml",
    )
    assert created.status_code == 201
    application_id = created.json()["id"]
    assert (await client.get(APPLICATIONS)).json()["total"] == 0

    reviewed = await approve(env, application_id)
    assert reviewed.status_code == 200
    private = reviewed.json()
    assert_private_shape(private)
    assert private["status"] == "approved"
    assert private["friend_id"] is not None
    assert private["reviewed_at"] is not None
    assert private["review_note"] == ""
    assert private["email"] == "owner@example.com"
    friend_id = private["friend_id"]

    public = await client.get(APPLICATIONS)
    assert public.json()["total"] == 1
    public_item = public.json()["items"][0]
    assert_public_shape(public_item)
    assert public_item["id"] == application_id
    assert public_item["friend_id"] == friend_id
    assert public_item["name"] == "申请站"
    assert public_item["rss_url"] == "https://approved.example.com/rss.xml"
    assert "owner@example.com" not in public.text

    formal = await client.get("/api/v1/friends")
    assert formal.json()["total"] == 1
    friend = formal.json()["items"][0]
    assert friend["id"] == friend_id
    assert friend["name"] == "申请站"
    assert friend["url"] == "https://approved.example.com/"
    assert friend["avatar"] == "https://approved.example.com/avatar.png"
    assert friend["rss_url"] == "https://approved.example.com/rss.xml"
    assert friend["sort_order"] == 0
    assert "owner@example.com" not in formal.text

    data = snapshot(env)
    assert len(data) == 1
    assert data[0]["id"] == friend_id and data[0]["url"] == "https://approved.example.com/"
    assert data[0]["rss_url"] == "https://approved.example.com/rss.xml"
    assert "owner@example.com" not in env.path.read_text("utf-8")

    repeated = await approve(env, application_id)
    assert repeated.status_code == 200
    assert repeated.json()["friend_id"] == friend_id
    assert await row_count(env, Friend) == 1
    assert await row_count(env, FriendApplication) == 1
    assert len(snapshot(env)) == 1

    processed = await reject(env, application_id, "不应再处理")
    assert processed.status_code == 409
    assert processed.json()["detail"] == "申请已处理，请刷新列表"


@pytest.mark.asyncio
async def test_concurrent_approval_from_independent_sessions_creates_one_friend(friend_env):
    """两个独立请求会话同时批准同一申请，条件更新只允许一个成功转换。"""
    env = friend_env
    created = await submit_with(env, env.headers["a"], url="https://race-approve.example.com/")
    assert created.status_code == 201
    application_id = created.json()["id"]

    responses = await asyncio.gather(*(approve(env, application_id) for _ in range(2)))

    assert [response.status_code for response in responses] == [200, 200]
    friend_ids = {response.json()["friend_id"] for response in responses}
    assert len(friend_ids) == 1 and None not in friend_ids
    assert await row_count(env, Friend) == 1
    assert await row_count(env, FriendApplication) == 1
    stored_friend_id = await scalar_value(
        env, select(FriendApplication.friend_id).where(FriendApplication.id == application_id)
    )
    assert stored_friend_id == friend_ids.pop()
    assert len(snapshot(env)) == 1


@pytest.mark.asyncio
async def test_rejection_requires_reason_and_allows_same_site_resubmission(friend_env):
    """拒绝必须写明原因，私有原因仅本人/管理员可见，拒绝后站点可重新申请。"""
    env = friend_env
    client = env.client
    assert (await client.post("/api/v1/friends/sync-json", headers=env.headers["admin"])).status_code == 204
    assert snapshot(env) == []

    created = await submit_with(env, env.headers["a"], name="准备拒绝", url="https://retry.example.com/")
    assert created.status_code == 201
    application_id = created.json()["id"]

    assert (await reject(env, application_id)).status_code == 422
    assert (await reject(env, application_id, "   ")).status_code == 422
    assert (await reject(env, application_id, "x" * 501)).status_code == 422
    assert await scalar_value(
        env, select(FriendApplication.status).where(FriendApplication.id == application_id)
    ) == "pending"

    rejected = await reject(env, application_id, "   内容不符合要求   ")
    assert rejected.status_code == 200
    rejected_body = rejected.json()
    assert_private_shape(rejected_body)
    assert rejected_body["status"] == "rejected"
    assert rejected_body["review_note"] == "内容不符合要求"
    assert rejected_body["friend_id"] is None
    assert rejected_body["reviewed_at"] is not None
    assert await scalar_value(
        env, select(FriendApplication.active_site_key).where(FriendApplication.id == application_id)
    ) is None

    assert (await client.get(APPLICATIONS)).json()["total"] == 0
    assert (await client.get("/api/v1/friends")).json()["total"] == 0
    assert snapshot(env) == []

    mine = (await client.get(f"{APPLICATIONS}/mine", headers=env.headers["a"])).json()
    assert mine["total"] == 1
    assert mine["items"][0]["review_note"] == "内容不符合要求"
    assert (await client.get(f"{APPLICATIONS}/mine", headers=env.headers["b"])).json()["total"] == 0
    admin_rejected = (await client.get(
        f"{APPLICATIONS}/admin", headers=env.headers["admin"], params={"status": "rejected"}
    )).json()
    assert admin_rejected["total"] == 1
    assert admin_rejected["items"][0]["email"] == "owner@example.com"

    resubmitted = await submit_with(env, env.headers["a"], name="重新申请", url="https://retry.example.com/")
    assert resubmitted.status_code == 201
    new_id = resubmitted.json()["id"]
    assert new_id != application_id
    assert resubmitted.json()["status"] == "pending"
    assert await row_count(env, FriendApplication) == 2
    assert (await client.get(APPLICATIONS)).json()["total"] == 0

    assert (await approve(env, new_id)).status_code == 200
    public = (await client.get(APPLICATIONS)).json()
    assert public["total"] == 1 and public["items"][0]["id"] == new_id
    assert (await client.get("/api/v1/friends")).json()["total"] == 1
    assert len(snapshot(env)) == 1
    mine_after = (await client.get(f"{APPLICATIONS}/mine", headers=env.headers["a"])).json()
    assert {(item["id"], item["status"]) for item in mine_after["items"]} == {
        (application_id, "rejected"),
        (new_id, "approved"),
    }


@pytest.mark.asyncio
async def test_application_discussion_visibility_permissions_and_plaintext(friend_env):
    """待审/拒绝讨论不可读写；通过后登录用户可讨论，脚本内容只作为纯文本。"""
    env = friend_env
    client = env.client

    pending = await submit_with(env, env.headers["a"], url="https://discuss.example.com/")
    assert pending.status_code == 201
    pending_id = pending.json()["id"]
    pending_page = f"friend-application:{pending_id}"

    assert (await client.get(COMMENTS, params={"page_key": pending_page})).status_code == 404
    assert (await client.get(f"{COMMENTS}/count", params={"page_key": pending_page})).status_code == 404
    assert (await client.post(
        COMMENTS, headers=env.headers["b"], json={"page_key": pending_page, "content": "待审回复"}
    )).status_code == 404
    assert (await client.post(
        COMMENTS, headers=env.headers["admin"], json={"page_key": pending_page, "content": "管理员待审回复"}
    )).status_code == 404
    assert (await client.post(
        COMMENTS, json={"page_key": pending_page, "content": "匿名回复"}
    )).status_code == 401

    signed_overflow = "friend-application:9223372036854775808"
    enormous_id = "friend-application:" + "9" * 40
    malformed_keys = [
        pending_page,
        "friend-application:9999",
        "friend-application:abc",
        "friend-application:0",
        "friend-application:01",
        signed_overflow,
        enormous_id,
    ]
    hidden_batch = await client.post(f"{COMMENTS}/batch-count", json={"page_keys": malformed_keys})
    assert hidden_batch.status_code == 200
    assert hidden_batch.json() == {key: 0 for key in malformed_keys}
    for key in (signed_overflow, enormous_id):
        assert (await client.get(COMMENTS, params={"page_key": key})).status_code == 404
        assert (await client.get(f"{COMMENTS}/count", params={"page_key": key})).status_code == 404
        assert (await client.post(
            COMMENTS, headers=env.headers["b"], json={"page_key": key, "content": "超大 ID 回复"}
        )).status_code == 404
    assert await row_count(env, Comment) == 0

    assert (await approve(env, pending_id)).status_code == 200
    page = pending_page
    assert (await client.get(COMMENTS, params={"page_key": page})).json()["total"] == 0

    root_response = await client.post(
        COMMENTS, headers=env.headers["b"], json={"page_key": page, "content": "欢迎互访"}
    )
    assert root_response.status_code == 201
    root_id = root_response.json()["id"]
    reply_response = await client.post(
        COMMENTS, headers=env.headers["a"],
        json={"page_key": page, "content": "谢谢，已经添加", "parent_id": root_id},
    )
    assert reply_response.status_code == 201
    reply_id = reply_response.json()["id"]

    anonymous_tree = (await client.get(COMMENTS, params={"page_key": page})).json()
    assert anonymous_tree["total"] == 2
    assert len(anonymous_tree["items"]) == 1
    assert anonymous_tree["items"][0]["content"] == "欢迎互访"
    assert anonymous_tree["items"][0]["can_delete"] is False
    assert anonymous_tree["items"][0]["children"][0]["content"] == "谢谢，已经添加"

    script_text = '<script>alert("x")</script>'
    script_response = await client.post(
        COMMENTS, headers=env.headers["b"], json={"page_key": page, "content": script_text}
    )
    assert script_response.status_code == 201
    assert script_response.headers["content-type"].startswith("application/json")
    assert script_response.json()["content"] == script_text
    script_id = script_response.json()["id"]
    listed = (await client.get(COMMENTS, params={"page_key": page})).json()
    assert script_text in [item["content"] for item in listed["items"]]

    second = await submit_with(env, env.headers["b"], name="第二申请", url="https://second.example.com/")
    assert second.status_code == 201
    second_id = second.json()["id"]
    assert (await approve(env, second_id)).status_code == 200
    second_page = f"friend-application:{second_id}"
    second_root = await client.post(
        COMMENTS, headers=env.headers["b"], json={"page_key": second_page, "content": "第二页根评论"}
    )
    assert second_root.status_code == 201
    second_root_id = second_root.json()["id"]
    assert (await client.post(
        COMMENTS, headers=env.headers["a"],
        json={"page_key": second_page, "content": "跨页回复", "parent_id": root_id},
    )).status_code == 400
    assert (await client.post(
        COMMENTS, headers=env.headers["a"],
        json={"page_key": "about", "content": "跨页回复", "parent_id": root_id},
    )).status_code == 400
    assert (await client.post(
        COMMENTS, headers=env.headers["a"],
        json={"page_key": second_page, "content": "第二页正常回复", "parent_id": second_root_id},
    )).status_code == 201

    about = await client.post(
        COMMENTS, headers=env.headers["b"], json={"page_key": "about", "content": "普通页面评论"}
    )
    assert about.status_code == 201
    assert (await client.get(COMMENTS, params={"page_key": "about"})).json()["total"] == 1

    rejected = await submit_with(env, env.headers["a"], name="拒绝讨论", url="https://rejected-talk.example.com/")
    rejected_id = rejected.json()["id"]
    assert (await reject(env, rejected_id, "不予通过")).status_code == 200
    rejected_page = f"friend-application:{rejected_id}"
    assert (await client.get(COMMENTS, params={"page_key": rejected_page})).status_code == 404
    assert (await client.get(f"{COMMENTS}/count", params={"page_key": rejected_page})).status_code == 404
    assert (await client.post(
        COMMENTS, headers=env.headers["b"], json={"page_key": rejected_page, "content": "不应写入"}
    )).status_code == 404
    assert await row_count(env, Comment, Comment.page_key == rejected_page) == 0

    batch_keys = [page, second_page, "about", rejected_page, pending_page + "0", "friend-application:9999"]
    batch = await client.post(f"{COMMENTS}/batch-count", json={"page_keys": batch_keys})
    assert batch.status_code == 200
    counts = batch.json()
    assert counts[page] == 3
    assert counts[second_page] == 2
    assert counts["about"] == 1
    assert counts[rejected_page] == 0
    assert counts[pending_page + "0"] == 0
    assert counts["friend-application:9999"] == 0

    assert (await client.delete(f"{COMMENTS}/{root_id}", headers=env.headers["a"])).status_code == 403
    assert (await client.delete(f"{COMMENTS}/{reply_id}", headers=env.headers["b"])).status_code == 403
    assert (await client.delete(f"{COMMENTS}/{root_id}", headers=env.headers["admin"])).status_code == 204
    after_admin_delete = (await client.get(COMMENTS, params={"page_key": page})).json()
    assert after_admin_delete["total"] == 1
    assert after_admin_delete["items"][0]["id"] == script_id
    assert (await client.delete(f"{COMMENTS}/{script_id}", headers=env.headers["admin"])).status_code == 204
    assert (await client.get(COMMENTS, params={"page_key": page})).json()["total"] == 0


@pytest.mark.asyncio
async def test_linked_friend_update_syncs_application_and_rolls_back_invalid_changes(friend_env):
    """编辑申请来源友链会同步公开申请与 JSON，非法或冲突修改整体回滚。"""
    env = friend_env
    client = env.client

    created = await submit_with(
        env,
        env.headers["a"],
        name="原名称",
        url="https://linked.example.com/",
        avatar="https://linked.example.com/avatar.png",
        rss_url="https://linked.example.com/feed.xml",
    )
    application_id = created.json()["id"]
    approved = await approve(env, application_id)
    friend_id = approved.json()["friend_id"]

    other = await client.post(
        "/api/v1/friends",
        headers=env.headers["admin"],
        json={"name": "其他站", "url": "https://other.example.com/"},
    )
    assert other.status_code == 201

    updated = await client.put(
        f"/api/v1/friends/{friend_id}",
        headers=env.headers["admin"],
        json={
            "name": "更新后的名称",
            "url": "https://linked-updated.example.com/",
            "avatar": "https://linked.example.com/new.png",
            "rss_url": "https://linked.example.com/rss.xml",
            "bio": "新简介",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "更新后的名称"
    assert updated.json()["url"] == "https://linked-updated.example.com/"
    assert updated.json()["avatar"] == "https://linked.example.com/new.png"
    assert updated.json()["rss_url"] == "https://linked.example.com/rss.xml"
    assert updated.json()["bio"] == "新简介"

    public_item = (await client.get(APPLICATIONS)).json()["items"][0]
    assert public_item["name"] == "更新后的名称"
    assert public_item["url"] == "https://linked-updated.example.com/"
    assert public_item["avatar"] == "https://linked.example.com/new.png"
    assert public_item["rss_url"] == "https://linked.example.com/rss.xml"
    formal_item = {
        item["id"]: item for item in (await client.get("/api/v1/friends")).json()["items"]
    }[friend_id]
    assert formal_item["name"] == "更新后的名称"
    assert formal_item["url"] == "https://linked-updated.example.com/"
    assert formal_item["avatar"] == "https://linked.example.com/new.png"
    assert formal_item["rss_url"] == "https://linked.example.com/rss.xml"
    mine_item = (await client.get(f"{APPLICATIONS}/mine", headers=env.headers["a"])).json()["items"][0]
    assert mine_item["name"] == "更新后的名称"
    assert mine_item["url"] == "https://linked-updated.example.com/"
    assert mine_item["rss_url"] == "https://linked.example.com/rss.xml"
    assert mine_item["email"] == "owner@example.com"
    updated_snapshot = {item["id"]: item for item in snapshot(env)}
    assert updated_snapshot[friend_id]["name"] == "更新后的名称"
    assert updated_snapshot[friend_id]["url"] == "https://linked-updated.example.com/"
    assert updated_snapshot[friend_id]["rss_url"] == "https://linked.example.com/rss.xml"

    stable_snapshot = env.path.read_bytes()
    stable_friend = await scalar_value(env, select(Friend).where(Friend.id == friend_id))
    stable_name, stable_url = stable_friend.name, stable_friend.url

    assert (await client.put(
        f"/api/v1/friends/{friend_id}",
        headers=env.headers["admin"],
        json={"name": "   ", "url": "https://never.example.com/"},
    )).status_code == 422
    assert (await client.put(
        f"/api/v1/friends/{friend_id}",
        headers=env.headers["admin"],
        json={"rss_url": "ftp://linked.example.com/rss.xml"},
    )).status_code == 422
    assert (await client.put(
        f"/api/v1/friends/{friend_id}",
        headers=env.headers["admin"],
        json={"avatar": "https://linked.example.com/a b.png"},
    )).status_code == 422
    assert env.path.read_bytes() == stable_snapshot
    unchanged = await scalar_value(env, select(Friend).where(Friend.id == friend_id))
    assert (unchanged.name, unchanged.url) == (stable_name, stable_url)

    collision = await client.put(
        f"/api/v1/friends/{friend_id}",
        headers=env.headers["admin"],
        json={"name": "不应保存", "url": "https://other.example.com/#fragment"},
    )
    assert collision.status_code == 409
    assert collision.json()["detail"] == "该站点已在友链中"
    still = await scalar_value(env, select(Friend).where(Friend.id == friend_id))
    assert (still.name, still.url) == (stable_name, stable_url)
    assert env.path.read_bytes() == stable_snapshot

    pending = await submit_with(env, env.headers["b"], name="占位申请", url="https://pending.example.com/")
    assert pending.status_code == 201
    pending_id = pending.json()["id"]
    unique_conflict = await client.put(
        f"/api/v1/friends/{friend_id}",
        headers=env.headers["admin"],
        json={"name": "不应保存2", "url": "https://pending.example.com/"},
    )
    assert unique_conflict.status_code == 409
    assert unique_conflict.json()["detail"] == "该站点已有待审核或已通过的申请"
    still = await scalar_value(env, select(Friend).where(Friend.id == friend_id))
    assert (still.name, still.url) == (stable_name, stable_url)
    pending_key = await scalar_value(
        env, select(FriendApplication.active_site_key).where(FriendApplication.id == pending_id)
    )
    assert pending_key == "https://pending.example.com/"
    assert env.path.read_bytes() == stable_snapshot

    null_rss = await client.put(
        f"/api/v1/friends/{friend_id}", headers=env.headers["admin"], json={"rss_url": None}
    )
    assert null_rss.status_code == 200 and null_rss.json()["rss_url"] == "https://linked.example.com/rss.xml"
    cleared = await client.put(
        f"/api/v1/friends/{friend_id}", headers=env.headers["admin"], json={"rss_url": ""}
    )
    assert cleared.status_code == 200 and cleared.json()["rss_url"] == ""
    assert (await client.get(APPLICATIONS)).json()["items"][0]["rss_url"] == ""
    formal_cleared = {
        item["id"]: item for item in (await client.get("/api/v1/friends")).json()["items"]
    }[friend_id]
    assert formal_cleared["rss_url"] == ""
    cleared_snapshot = {item["id"]: item for item in snapshot(env)}
    assert cleared_snapshot[friend_id]["rss_url"] == ""
    assert (await client.get(f"{APPLICATIONS}/mine", headers=env.headers["a"])).json()["items"][0][
        "email"
    ] == "owner@example.com"


@pytest.mark.asyncio
async def test_deleting_application_or_friend_removes_comments_and_snapshot(friend_env):
    """两个删除入口都清理申请、正式友链、讨论和 JSON。"""
    env = friend_env
    client = env.client

    pending = await submit_with(env, env.headers["a"], url="https://delete-pending.example.com/")
    pending_id = pending.json()["id"]
    assert (await client.delete(f"{APPLICATIONS}/{pending_id}", headers=env.headers["admin"])).status_code == 204
    assert await row_count(env, FriendApplication) == 0
    assert (await client.delete(f"{APPLICATIONS}/{pending_id}", headers=env.headers["admin"])).status_code == 404

    first = await submit_with(env, env.headers["a"], name="删除申请站", url="https://delete-one.example.com/")
    first_id = first.json()["id"]
    first_friend_id = (await approve(env, first_id)).json()["friend_id"]
    first_page = f"friend-application:{first_id}"
    root = await client.post(
        COMMENTS, headers=env.headers["b"], json={"page_key": first_page, "content": "删除前回复"}
    )
    assert root.status_code == 201
    reply = await client.post(
        COMMENTS, headers=env.headers["a"],
        json={"page_key": first_page, "content": "删除前子回复", "parent_id": root.json()["id"]},
    )
    assert reply.status_code == 201
    assert len(snapshot(env)) == 1

    assert (await client.delete(f"{APPLICATIONS}/{first_id}", headers=env.headers["admin"])).status_code == 204
    assert await row_count(env, FriendApplication) == 0
    assert await row_count(env, Friend) == 0
    assert await row_count(env, Comment, Comment.page_key == first_page) == 0
    assert (await client.get(APPLICATIONS)).json() == {"items": [], "total": 0}
    assert (await client.get("/api/v1/friends")).json()["total"] == 0
    assert snapshot(env) == []
    assert (await client.get(COMMENTS, params={"page_key": first_page})).status_code == 404
    assert (await client.get(f"{COMMENTS}/count", params={"page_key": first_page})).status_code == 404

    second = await submit_with(env, env.headers["b"], name="删除友链站", url="https://delete-two.example.com/")
    second_id = second.json()["id"]
    second_friend_id = (await approve(env, second_id)).json()["friend_id"]
    second_page = f"friend-application:{second_id}"
    second_comment = await client.post(
        COMMENTS, headers=env.headers["b"], json={"page_key": second_page, "content": "友链删除前"}
    )
    assert second_comment.status_code == 201
    assert len(snapshot(env)) == 1

    assert (await client.delete(
        f"/api/v1/friends/{second_friend_id}", headers=env.headers["admin"]
    )).status_code == 204
    assert await row_count(env, FriendApplication) == 0
    assert await row_count(env, Friend) == 0
    assert await row_count(env, Comment, Comment.page_key == second_page) == 0
    assert (await client.get(APPLICATIONS)).json()["total"] == 0
    assert (await client.get("/api/v1/friends")).json()["total"] == 0
    assert snapshot(env) == []
    assert (await client.get(COMMENTS, params={"page_key": second_page})).status_code == 404


@pytest.mark.asyncio
async def test_account_deletion_retains_pending_approved_and_rejected_history(friend_env):
    """删除申请账户后历史保留为已注销用户，已通过申请仍公开且 JSON 不变。"""
    env = friend_env
    client = env.client

    approved = await submit_with(env, env.headers["a"], name="已通过", url="https://audit-approved.example.com/")
    approved_id = approved.json()["id"]
    approved_friend_id = (await approve(env, approved_id)).json()["friend_id"]
    pending = await submit_with(env, env.headers["a"], name="待审核", url="https://audit-pending.example.com/")
    pending_id = pending.json()["id"]
    rejected = await submit_with(env, env.headers["a"], name="未通过", url="https://audit-rejected.example.com/")
    rejected_id = rejected.json()["id"]
    assert (await reject(env, rejected_id, "资料不足")).status_code == 200
    assert len(snapshot(env)) == 1

    assert (await client.delete("/api/v1/users/1", headers=env.headers["admin"])).status_code == 204

    admin_list = (await client.get(f"{APPLICATIONS}/admin", headers=env.headers["admin"])).json()
    assert admin_list["total"] == 3
    by_id = {item["id"]: item for item in admin_list["items"]}
    assert set(by_id) == {approved_id, pending_id, rejected_id}
    assert all(item["user_id"] is None for item in by_id.values())
    assert all(item["email"] == "owner@example.com" for item in by_id.values())
    assert by_id[approved_id]["status"] == "approved"
    assert by_id[approved_id]["friend_id"] == approved_friend_id
    assert by_id[pending_id]["status"] == "pending"
    assert by_id[rejected_id]["status"] == "rejected"
    assert by_id[rejected_id]["review_note"] == "资料不足"

    assert await row_count(env, FriendApplication) == 3
    assert await row_count(env, FriendApplication, FriendApplication.user_id.is_(None)) == 3
    assert (await client.get(f"{APPLICATIONS}/mine", headers=env.headers["a"])).status_code == 401

    public = await client.get(APPLICATIONS)
    assert public.json()["total"] == 1
    assert public.json()["items"][0]["id"] == approved_id
    assert "owner@example.com" not in public.text
    assert (await client.get("/api/v1/friends")).json()["total"] == 1
    data = snapshot(env)
    assert len(data) == 1 and data[0]["id"] == approved_friend_id
    assert "owner@example.com" not in env.path.read_text("utf-8")

    rejected_page = f"friend-application:{rejected_id}"
    assert (await client.get(COMMENTS, params={"page_key": rejected_page})).status_code == 404
    assert (await client.post(
        f"{COMMENTS}/batch-count", json={"page_keys": [rejected_page]}
    )).json()[rejected_page] == 0


@pytest.mark.asyncio
async def test_concurrent_reply_and_delete_leave_no_orphan_comments(friend_env):
    """回复持有写锁时删除等待；真实 HTTP 竞态下删除成功也绝不留下孤儿评论。"""
    env = friend_env
    client = env.client

    created = await submit_with(env, env.headers["a"], url="https://race-delete.example.com/")
    application_id = created.json()["id"]
    friend_id = (await approve(env, application_id)).json()["friend_id"]
    page = f"friend-application:{application_id}"

    reply_session = env.sessions()
    delete_session = env.sessions()
    delete_started = asyncio.Event()
    try:
        assert await friend_service.lock_application(reply_session, application_id, approved_only=True) is True
        reply_session.add(Comment(page_key=page, user_id=2, content="并发中的回复"))
        await reply_session.flush()

        async def delete_when_started():
            delete_started.set()
            return await delete_application(delete_session, application_id)

        delete_task = asyncio.create_task(delete_when_started())
        await asyncio.wait_for(delete_started.wait(), timeout=5)
        await asyncio.sleep(0.05)
        assert not delete_task.done()

        await reply_session.commit()
        assert await asyncio.wait_for(delete_task, timeout=10) is True
        await friend_service.commit_friend_changes(delete_session)
    finally:
        await reply_session.close()
        await delete_session.close()

    assert friend_id is not None
    assert await row_count(env, FriendApplication) == 0
    assert await row_count(env, Friend) == 0
    assert await row_count(env, Comment, Comment.page_key == page) == 0
    assert snapshot(env) == []

    second = await submit_with(env, env.headers["b"], url="https://race-http.example.com/")
    second_id = second.json()["id"]
    assert (await approve(env, second_id)).status_code == 200
    second_page = f"friend-application:{second_id}"
    barrier = asyncio.Event()

    async def send_reply():
        await barrier.wait()
        return await client.post(
            COMMENTS, headers=env.headers["b"], json={"page_key": second_page, "content": "竞态回复"}
        )

    async def remove_application():
        await barrier.wait()
        return await client.delete(f"{APPLICATIONS}/{second_id}", headers=env.headers["admin"])

    barrier.set()
    reply_response, delete_response = await asyncio.gather(send_reply(), remove_application())
    assert delete_response.status_code == 204
    assert reply_response.status_code in (201, 404)
    assert await row_count(env, FriendApplication) == 0
    assert await row_count(env, Friend) == 0
    assert await row_count(env, Comment, Comment.page_key == second_page) == 0
    assert snapshot(env) == []


@pytest.mark.asyncio
async def test_deleted_authenticated_account_cannot_assign_application_to_reused_id(friend_env):
    """认证完成后账户被删除，SQLite 复用 ID 也不能把私有申请交给新用户。"""
    env = friend_env
    async with env.sessions() as setup:
        original = User(username="deleted-during-submit", email="old-owner@example.com", password_hash="original-hash")
        setup.add(original)
        await setup.commit()
        original_id = original.id
    async with env.sessions() as authenticated_request:
        authenticated_user = await authenticated_request.get(User, original_id)
        assert (await env.client.delete(f"/api/v1/users/{original_id}", headers=env.headers["admin"])).status_code == 204
        async with env.sessions() as registration:
            replacement = User(username="replacement-account", email="new-owner@example.com", password_hash="new-hash")
            registration.add(replacement)
            await registration.commit()
            assert replacement.id == original_id
        with pytest.raises(HTTPException) as failure:
            await create_application(
                authenticated_request, authenticated_user,
                FriendApplicationCreate(**application_payload(email="private-contact@example.com")),
            )
        assert failure.value.status_code == 401
    assert await row_count(env, FriendApplication) == 0


@pytest.mark.asyncio
async def test_deleted_application_id_never_targets_a_new_application(friend_env):
    """旧审核确认与旧讨论地址在删除后始终失效，不命中新申请。"""
    env = friend_env
    first = await submit_with(env, env.headers["a"], url="https://first-id.example.com/")
    first_id = first.json()["id"]
    assert (await env.client.delete(f"{APPLICATIONS}/{first_id}", headers=env.headers["admin"])).status_code == 204
    second = await submit_with(env, env.headers["b"], url="https://new-id.example.com/")
    second_id = second.json()["id"]
    assert second_id != first_id
    assert (await approve(env, first_id)).status_code == 404
    assert (await env.client.get(COMMENTS, params={"page_key": f"friend-application:{first_id}"})).status_code == 404
    assert (await env.client.get(f"{APPLICATIONS}/mine", headers=env.headers["b"])).json()["items"][0]["status"] == "pending"

"""评论线程的真实 HTTP 深度、目标元数据、权限与旧数据回归。"""

import asyncio
from datetime import datetime

import pytest
from sqlalchemy import select

from app.config import settings
from app.models.comment import Comment
from app.models.user import User
from tests.test_friend_snapshot import friend_env  # noqa: F401

COMMENTS = "/api/v1/comments"


@pytest.mark.asyncio
async def test_1200_deep_thread_is_flat_complete_and_deletable(friend_env):
    """1200 层数据库关系只序列化两层，并保留全部 ID 和真实回复目标。"""
    env = friend_env
    timestamp = datetime(2026, 1, 1, 12, 0)
    async with env.sessions() as db:
        db.add_all([
            Comment(
                id=comment_id, page_key="post:deep-thread", user_id=1,
                parent_id=comment_id - 1 if comment_id > 1 else None,
                content=f"深层评论 {comment_id}", created_at=timestamp,
            )
            for comment_id in range(1, 1202)
        ])
        await db.commit()

    response = await env.client.get(COMMENTS, params={"page_key": "post:deep-thread"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1201
    assert len(body["items"]) == 1
    root = body["items"][0]
    assert root["id"] == 1
    assert root["parent_id"] is None and root["reply_to_author"] == ""
    assert [reply["id"] for reply in root["children"]] == list(range(2, 1202))
    assert all(reply["children"] == [] for reply in root["children"])
    assert all(reply["parent_id"] == reply["id"] - 1 for reply in root["children"])
    assert all(reply["reply_to_author"] == "a" for reply in root["children"])
    assert not root["can_delete"]
    async with env.sessions() as db:
        stored = dict((await db.execute(select(Comment.id, Comment.parent_id))).all())
    assert stored == {comment_id: comment_id - 1 if comment_id > 1 else None for comment_id in range(1, 1202)}

    forbidden = await env.client.delete(f"{COMMENTS}/1", headers=env.headers["b"])
    assert forbidden.status_code == 403
    deleted = await asyncio.wait_for(
        env.client.delete(f"{COMMENTS}/1", headers=env.headers["a"]), timeout=15,
    )
    assert deleted.status_code == 204
    assert (await env.client.get(COMMENTS, params={"page_key": "post:deep-thread"})).json() == {
        "items": [], "total": 0,
    }


@pytest.mark.asyncio
async def test_legacy_orphans_cycles_and_cross_page_parents_remain_readable_without_mutation(friend_env):
    """缺失父行、循环和跨页旧关联不会丢评论，也不会带出另一页的作者信息。"""
    env = friend_env
    timestamp = datetime(2026, 1, 1, 12, 0)
    parents = {10: None, 11: 10, 12: 999, 13: 12, 20: 21, 21: 20, 22: 21, 31: 30}
    async with env.sessions() as db:
        db.add(Comment(id=30, page_key="post:other", content="其他页面", legacy_author="私有目标", created_at=timestamp))
        db.add_all([
            Comment(
                id=comment_id, page_key="about", parent_id=parent_id,
                content=f"旧评论 {comment_id}", legacy_author=f"作者 {comment_id}", created_at=timestamp,
            )
            for comment_id, parent_id in parents.items()
        ])
        await db.commit()

    response = await env.client.get(COMMENTS, params={"page_key": "about"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == len(parents)
    assert [root["id"] for root in body["items"]] == [10, 12, 20, 31]
    nodes = [node for root in body["items"] for node in [root, *root["children"]]]
    assert sorted(node["id"] for node in nodes) == sorted(parents)
    assert all(child["children"] == [] for root in body["items"] for child in root["children"])
    assert all(root["parent_id"] is None and root["reply_to_author"] == "" for root in body["items"])
    assert "私有目标" not in response.text and "其他页面" not in response.text
    cycle = next(root for root in body["items"] if root["id"] == 20)
    assert [(child["id"], child["parent_id"], child["reply_to_author"]) for child in cycle["children"]] == [
        (21, 20, "作者 20"), (22, 21, "作者 21"),
    ]
    async with env.sessions() as db:
        stored = dict((await db.execute(select(Comment.id, Comment.parent_id).where(Comment.page_key == "about"))).all())
    assert stored == parents

    deleted = await asyncio.wait_for(
        env.client.delete(f"{COMMENTS}/20", headers=env.headers["admin"]), timeout=5,
    )
    assert deleted.status_code == 204
    remaining = (await env.client.get(COMMENTS, params={"page_key": "about"})).json()
    assert remaining["total"] == len(parents) - 3
    assert (await env.client.get(COMMENTS, params={"page_key": "post:other"})).json()["total"] == 1


@pytest.mark.asyncio
async def test_reply_to_child_preserves_target_without_reply_cap_and_keeps_permissions_and_page_isolation(friend_env):
    """第五条回复可发送；回复子评论保留该用户，而非悄悄改为根作者。"""
    env = friend_env
    async with env.sessions() as db:
        owner = await db.get(User, 1)
        replier = await db.get(User, 2)
        owner.display_name = "根作者"
        replier.display_name = "回复作者"
        await db.commit()
    created = await env.client.post(
        COMMENTS, headers=env.headers["a"], json={"page_key": "about", "content": "根评论"},
    )
    assert created.status_code == 201
    root = created.json()
    assert root["parent_id"] is None and root["reply_to_author"] == ""
    parent = root
    replies = []
    for index in range(5):
        response = await env.client.post(
            COMMENTS, headers=env.headers["b"],
            json={"page_key": "about", "content": f"回复 {index}", "parent_id": parent["id"]},
        )
        assert response.status_code == 201
        reply = response.json()
        assert reply["parent_id"] == parent["id"]
        assert reply["reply_to_author"] == parent["author"]
        assert reply["children"] == [] and reply["can_delete"] is True
        replies.append(reply)
        parent = reply

    listed = await env.client.get(COMMENTS, params={"page_key": "about"}, headers=env.headers["b"])
    assert listed.status_code == 200 and listed.json()["total"] == 6
    listed_root = listed.json()["items"][0]
    assert listed_root["can_delete"] is False
    assert [child["id"] for child in listed_root["children"]] == [reply["id"] for reply in replies]
    assert all(child["can_delete"] is True and child["children"] == [] for child in listed_root["children"])
    assert (await env.client.delete(f"{COMMENTS}/{root['id']}", headers=env.headers["b"])).status_code == 403
    assert (await env.client.delete(f"{COMMENTS}/{replies[0]['id']}", headers=env.headers["a"])).status_code == 403

    isolated = await env.client.post(
        COMMENTS, headers=env.headers["a"], json={"page_key": "post:another", "content": "另一页"},
    )
    assert isolated.status_code == 201
    cross_page = await env.client.post(
        COMMENTS, headers=env.headers["b"],
        json={"page_key": "post:another", "content": "不能跨页回复", "parent_id": replies[-1]["id"]},
    )
    assert cross_page.status_code == 400
    assert (await env.client.get(COMMENTS, params={"page_key": "post:another"})).json()["items"][0]["children"] == []
    assert (await env.client.get(COMMENTS, params={"page_key": "about"})).json()["total"] == 6


@pytest.mark.asyncio
async def test_comments_use_current_database_email_verification_state(friend_env, monkeypatch):
    """已签发令牌和客户端字段不能覆盖当前账户的邮箱验证状态。"""
    env = friend_env
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION", True)
    async with env.sessions() as db:
        user = await db.get(User, 1)
        user.email_verified = False
        await db.commit()
    denied = await env.client.post(
        COMMENTS, headers=env.headers["a"],
        json={"page_key": "about", "content": "不应写入", "email_verified": True},
    )
    assert denied.status_code == 403
    assert (await env.client.get(COMMENTS, params={"page_key": "about"})).json()["total"] == 0
    async with env.sessions() as db:
        user = await db.get(User, 1)
        user.email_verified = True
        await db.commit()
    accepted = await env.client.post(
        COMMENTS, headers=env.headers["a"], json={"page_key": "about", "content": "已验证"},
    )
    assert accepted.status_code == 201

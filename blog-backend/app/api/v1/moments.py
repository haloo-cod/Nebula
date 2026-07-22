"""
说说路由 — CRUD + 点赞 + 评论
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.deps import require_admin
from app.models.user import User
from app.schemas.moment import (
    MomentCommentCreate,
    MomentCommentResponse,
    MomentCreate,
    MomentListResponse,
    MomentResponse,
)
from app.services.moment import (
    add_moment_comment,
    create_moment,
    delete_moment,
    get_moment_by_id,
    get_moment_comments,
    get_moments,
    like_moment,
)

router = APIRouter(prefix="/moments", tags=["说说"])


@router.get("", response_model=MomentListResponse)
async def list_moments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    """获取说说列表（分页）"""
    items, total = get_moments(page, page_size)
    return MomentListResponse(items=items, total=total)


@router.get("/{moment_id}", response_model=MomentResponse)
async def get_one_moment(moment_id: int):
    """获取单条说说"""
    moment = get_moment_by_id(moment_id)
    if not moment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="说说不存在")
    return moment


@router.post("", response_model=MomentResponse, status_code=status.HTTP_201_CREATED)
async def create_new_moment(
    body: MomentCreate,
    _: User = Depends(require_admin),
):
    """发布说说（需认证）"""
    moment = create_moment(
        content=body.content,
        mood=body.mood,
        tags=body.tags,
        images=body.images,
    )
    return moment


@router.delete("/{moment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_moment(
    moment_id: int,
    _: User = Depends(require_admin),
):
    """删除说说（需认证）"""
    success = delete_moment(moment_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="说说不存在")


@router.post("/{moment_id}/like")
async def like(moment_id: int, request: Request):
    """点赞说说（基于 IP 去重）"""
    client_ip = request.client.host if request.client else "unknown"
    likes = like_moment(moment_id, client_ip)
    if likes == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="说说不存在")
    return {"likes": likes}


@router.get("/{moment_id}/comments", response_model=list[MomentCommentResponse])
async def list_moment_comments(moment_id: int):
    """获取说说评论"""
    comments = get_moment_comments(moment_id)
    return comments


@router.post(
    "/{moment_id}/comments",
    response_model=MomentCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment(moment_id: int, body: MomentCommentCreate):
    """给说说添加评论（无需认证）"""
    comment = add_moment_comment(moment_id, body.nickname, body.content)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="说说不存在")
    return comment

"""后台用户管理相关 schemas。"""

from datetime import datetime

from pydantic import BaseModel, Field


class UserAdminItem(BaseModel):
    """管理员用户列表项。"""

    id: int
    username: str
    email: str | None
    display_name: str
    avatar_url: str
    github_id: str | None
    email_verified: bool
    is_admin: bool
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserAdminListResponse(BaseModel):
    """分页用户列表。"""

    items: list[UserAdminItem]
    total: int


class UserAdminUpdate(BaseModel):
    """管理员可修改的用户状态和基础资料。"""

    email: str | None = None
    display_name: str = Field(min_length=1, max_length=100)
    email_verified: bool
    is_admin: bool
    is_active: bool


class UserPasswordReset(BaseModel):
    """管理员重置用户密码。"""

    password: str = Field(min_length=8, max_length=128)

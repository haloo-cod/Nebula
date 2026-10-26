"""
友链相关 Pydantic schemas
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator, BaseModel, BeforeValidator, ConfigDict, EmailStr, Field,
    HttpUrl, TypeAdapter, field_validator, model_validator,
)


def trim_input(value):
    """统一移除用户输入的首尾空白。"""
    return value.strip() if isinstance(value, str) else value


def validate_http_url(value: str) -> str:
    """校验完整地址，拒绝凭据和内嵌空白，保存原字符串。"""
    if not value.lower().startswith(("http://", "https://")) or any(char.isspace() for char in value):
        raise ValueError("链接必须是完整的 HTTP 或 HTTPS 地址")
    parsed = TypeAdapter(HttpUrl).validate_python(value)
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("链接不能包含用户名或密码")
    return value


def validate_optional_url(value: str) -> str:
    """空地址表示不提供 RSS。"""
    return validate_http_url(value) if value else value


OptionalRssUrl = Annotated[
    str, Field(max_length=2048), BeforeValidator(trim_input), AfterValidator(validate_optional_url),
]
ApplicationName = Annotated[str, Field(min_length=1, max_length=100), BeforeValidator(trim_input)]
ApplicationUrl = Annotated[
    str, Field(min_length=1, max_length=500), BeforeValidator(trim_input), AfterValidator(validate_http_url),
]
ApplicationStatus = Literal["pending", "approved", "rejected"]


class FriendExchangeInfo(BaseModel):
    """交换友链展示信息。"""

    name: str = ""
    url: str = ""
    avatar: str = ""
    bio: str = ""
    requirements: list[str] = []
    contact: str = ""
    rss_url: str = Field(default="", max_length=2048)

    @field_validator("rss_url", mode="before")
    @classmethod
    def trim_rss_url(cls, value):
        """移除首尾空白，空字符串表示使用本站订阅源。"""
        return value.strip() if isinstance(value, str) else value

    @field_validator("rss_url")
    @classmethod
    def validate_rss_url(cls, value: str) -> str:
        """只接受完整 HTTP(S) 地址，并保留原始路径和查询参数。"""
        if value:
            if not value.lower().startswith(("http://", "https://")) or any(char.isspace() for char in value):
                raise ValueError("RSS 链接必须是完整的 HTTP 或 HTTPS 地址")
            TypeAdapter(HttpUrl).validate_python(value)
        return value


class FriendCreate(BaseModel):
    """创建友链（管理员）"""
    name: str
    bio: str = ""
    avatar: str = ""
    url: str
    sort_order: int = 0
    rss_url: OptionalRssUrl = ""


class FriendUpdate(BaseModel):
    """更新友链（管理员）"""
    name: str | None = None
    bio: str | None = None
    avatar: str | None = None
    url: str | None = None
    sort_order: int | None = None
    rss_url: OptionalRssUrl | None = None


class FriendResponse(BaseModel):
    """友链响应"""
    id: int
    name: str
    bio: str
    avatar: str
    url: str
    rss_url: OptionalRssUrl = ""
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FriendListResponse(BaseModel):
    """友链列表响应"""
    items: list[FriendResponse]
    total: int


class FriendApplicationCreate(BaseModel):
    """登录用户提交的站点与联络信息。"""
    model_config = ConfigDict(extra="forbid")

    name: ApplicationName
    url: ApplicationUrl
    avatar: ApplicationUrl
    email: Annotated[EmailStr, Field(min_length=1, max_length=320), BeforeValidator(trim_input)]
    rss_url: OptionalRssUrl = ""


class FriendApplicationReview(BaseModel):
    """仅待审核申请可接受管理员决策。"""
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approved", "rejected"]
    reason: Annotated[str, Field(max_length=500), BeforeValidator(trim_input)] = ""

    @model_validator(mode="after")
    def require_rejection_reason(self):
        if self.decision == "rejected" and not self.reason:
            raise ValueError("拒绝申请时必须填写原因")
        if self.decision == "approved":
            self.reason = ""
        return self


class FriendApplicationPublic(BaseModel):
    """只用于已通过且仍关联正式友链的公开记录。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    avatar: str
    rss_url: str
    created_at: datetime
    reviewed_at: datetime
    friend_id: int


class FriendApplicationPrivate(BaseModel):
    """仅申请本人及管理员可读取的完整申请。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    avatar: str
    rss_url: str
    created_at: datetime
    reviewed_at: datetime | None
    friend_id: int | None
    email: str
    user_id: int | None
    status: ApplicationStatus
    review_note: str


class FriendApplicationListResponse(BaseModel):
    """公开申请分页。"""
    items: list[FriendApplicationPublic]
    total: int


class FriendApplicationPrivateListResponse(BaseModel):
    """本人和管理端申请分页。"""
    items: list[FriendApplicationPrivate]
    total: int

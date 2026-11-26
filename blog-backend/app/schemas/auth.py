"""
认证相关 Pydantic schemas
"""

from pydantic import BaseModel, field_validator

from app.utils.security import validate_password_length


class LoginRequest(BaseModel):
    username: str
    password: str


class GithubLinkConfirmRequest(BaseModel):
    """使用现有账户密码确认 GitHub 绑定。"""

    link_token: str
    password: str


class RegisterRequest(BaseModel):
    """用户名、邮箱和密码注册。"""

    username: str
    email: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()
        if not 3 <= len(value) <= 30 or not all(char.isalnum() or char in "_-" for char in value):
            raise ValueError("用户名需为 3-30 位字母、数字、下划线或连字符")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if len(value) > 320 or "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("邮箱格式不正确")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_length(value)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    """注册结果；开启邮箱验证时不包含登录令牌。"""

    access_token: str | None = None
    token_type: str = "bearer"
    requires_email_verification: bool = False
    email: str | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    email: str | None = None
    display_name: str = ""
    avatar_url: str = ""
    email_verified: bool = False

    model_config = {"from_attributes": True}

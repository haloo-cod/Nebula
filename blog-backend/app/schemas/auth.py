"""
认证相关 Pydantic schemas
"""

from pydantic import BaseModel, field_validator


class LoginRequest(BaseModel):
    username: str
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
        if not 8 <= len(value) <= 128:
            raise ValueError("密码长度需为 8-128 位")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    email: str | None = None
    display_name: str = ""
    avatar_url: str = ""
    email_verified: bool = False

    model_config = {"from_attributes": True}

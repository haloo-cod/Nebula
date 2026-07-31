"""
CORS 中间件配置
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


def setup_cors(app: FastAPI) -> None:
    if settings.CORS_ALLOW_ALL:
        # 开发模式:反射任意 Origin。因为同时启用 allow_credentials=True,
        # 不能用 allow_origins=["*"](浏览器会拒绝带凭证的通配响应),
        # 改用 allow_origin_regex 匹配所有来源,实现"回显 Origin"效果。
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=".*",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        return

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

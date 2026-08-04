"""
CORS 中间件配置
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


def setup_cors(app: FastAPI) -> None:
    # 局域网开发需要开放任意 Origin 时,可将下面分支恢复并在开发环境配置
    # CORS_ALLOW_ALL=true。生产环境保持白名单,不要启用任意 Origin + credentials。
    # if settings.CORS_ALLOW_ALL:
    #     app.add_middleware(
    #         CORSMiddleware,
    #         allow_origin_regex=".*",
    #         allow_credentials=True,
    #         allow_methods=["*"],
    #         allow_headers=["*"],
    #     )
    #     return

    origins = list(settings.CORS_ORIGINS)
    # 本地开发常用 localhost 与 127.0.0.1 交替访问；两者是不同 Origin。
    # 仅在开发环境补充回环地址，生产仍严格使用配置白名单。
    if settings.ENVIRONMENT.lower() not in {"production", "prod"}:
        for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
            if origin not in origins:
                origins.append(origin)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

"""
CORS 中间件配置
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


def setup_cors(app: FastAPI) -> None:
    # 局域网开发需要开放任意 Origin 时，可恢复下面分支并在配置中启用
    # CORS_ALLOW_ALL=true。生产环境保持白名单，不要启用任意 Origin + credentials。
    # if settings.CORS_ALLOW_ALL:
    #     app.add_middleware(
    #         CORSMiddleware,
    #         allow_origin_regex=".*",
    #         allow_credentials=True,
    #         allow_methods=["*"],
    #         allow_headers=["*"],
    #     )
    #     return

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

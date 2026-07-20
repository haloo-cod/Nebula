"""
v1 路由汇总
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.images import router as images_router
from app.api.v1.files import router as files_router
from app.api.v1.posts import router as posts_router
from app.api.v1.comments import router as comments_router
from app.api.v1.moments import router as moments_router
from app.api.v1.about import router as about_router
from app.api.v1.gallery import router as gallery_router
from app.api.v1.books import router as books_router
from app.api.v1.backgrounds import router as backgrounds_router
from app.api.v1.carousel import router as carousel_router
from app.api.v1.albums import router as albums_router
from app.api.v1.friends import router as friends_router
from app.api.v1.treasures import router as treasures_router
from app.api.v1.profile import router as profile_router
from app.api.v1.tavern import router as tavern_router
from app.api.v1.users import router as users_router
from app.api.v1.analytics import router as analytics_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(images_router)
router.include_router(files_router)
router.include_router(posts_router)
router.include_router(comments_router)
router.include_router(moments_router)
router.include_router(about_router)
router.include_router(gallery_router)
router.include_router(books_router)
router.include_router(backgrounds_router)
router.include_router(carousel_router)
router.include_router(albums_router)
router.include_router(friends_router)
router.include_router(treasures_router)
router.include_router(profile_router)
router.include_router(tavern_router)
router.include_router(users_router)
router.include_router(analytics_router)

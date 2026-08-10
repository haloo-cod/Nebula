"""Security checks for public background media and file deletion."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.v1 import files as files_api
from app.models import Base
from app.models.background import Background
from app.models.file import UploadedFile


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def add_file(db_session, *, mime_type="video/mp4", file_id=None):
    record = UploadedFile(
        id=file_id,
        filename="test-media.mp4",
        original_name="test-media.mp4",
        mime_type=mime_type,
        file_size=4,
    )
    db_session.add(record)
    await db_session.flush()
    return record


@pytest.mark.asyncio
async def test_public_media_requires_video_background_reference(db_session, tmp_path, monkeypatch):
    record = await add_file(db_session)
    path = tmp_path / record.filename
    path.write_bytes(b"data")
    monkeypatch.setattr(files_api, "get_file_path", lambda _: path)

    with pytest.raises(files_api.HTTPException) as error:
        await files_api.stream_file_media(record.id, db_session)
    assert error.value.status_code == 404

    db_session.add(
        Background(
            media_type="video",
            media_url=f"/api/v1/files/{record.id}/media",
            theme="dark",
            device="desktop",
        )
    )
    await db_session.commit()
    response = await files_api.stream_file_media(record.id, db_session)
    assert response.media_type == "video/mp4"


@pytest.mark.asyncio
async def test_public_media_rejects_non_video_even_when_referenced(db_session):
    record = await add_file(db_session, mime_type="application/zip")
    db_session.add(
        Background(
            media_type="video",
            media_url=f"/api/v1/files/{record.id}/media",
            theme="dark",
            device="desktop",
        )
    )
    await db_session.commit()

    with pytest.raises(files_api.HTTPException) as error:
        await files_api.stream_file_media(record.id, db_session)
    assert error.value.status_code == 415


@pytest.mark.asyncio
async def test_referenced_file_cannot_be_deleted(db_session, monkeypatch):
    record = await add_file(db_session)
    db_session.add(
        Background(
            media_type="video",
            media_url=f"/api/v1/files/{record.id}/media",
            theme="dark",
            device="desktop",
        )
    )
    await db_session.commit()
    deleted = False

    def fake_delete(_):
        nonlocal deleted
        deleted = True

    monkeypatch.setattr(files_api, "delete_file", fake_delete)
    with pytest.raises(files_api.HTTPException) as error:
        await files_api.remove_file(record.id, db_session, None)
    assert error.value.status_code == 409
    assert not deleted
    assert await db_session.get(UploadedFile, record.id) is not None


@pytest.mark.asyncio
async def test_unreferenced_file_can_be_deleted(db_session, monkeypatch):
    record = await add_file(db_session)
    deleted_names = []
    monkeypatch.setattr(files_api, "delete_file", deleted_names.append)
    await files_api.remove_file(record.id, db_session, None)
    assert deleted_names == [record.filename]
    assert await db_session.get(UploadedFile, record.id) is None

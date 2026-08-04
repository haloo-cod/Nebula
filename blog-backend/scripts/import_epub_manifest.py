"""按 EPUB 导入清单将书籍可恢复地导入 SQLite。

清单由 ``.epub-import/scan_epubs.py`` 生成；脚本不会读取或导入被扫描为
加密的文件，也不会覆盖已有 slug。每处理一批记录就提交一次，单本元数据或
封面损坏时只跳过该项，便于在大书库上重复执行。

运行示例::

    cd blog-backend
    .venv/bin/python -m scripts.import_epub_manifest \
      --manifest ../.epub-import/import-manifest.json \
      --database /tmp/blog-import.db
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.services.book import extract_cover_image, read_epub_metadata, title_from_filename


def parse_args() -> argparse.Namespace:
    """解析导入清单、数据库及批量大小参数。"""

    parser = argparse.ArgumentParser(description="导入 EPUB 清单到开发数据库")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--no-cover", action="store_true", help="跳过封面提取")
    return parser.parse_args()


def load_manifest(path: Path) -> list[dict[str, str]]:
    """读取并校验清单中的 source、target、slug 字段。"""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("导入清单必须是数组")
    result: list[dict[str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        source = item.get("source", "")
        target = item.get("target", "")
        slug = item.get("slug", "")
        if source and target and slug:
            result.append({"source": source, "target": target, "slug": slug})
    return result


def import_manifest(manifest: list[dict[str, str]], database: Path, batch_size: int, no_cover: bool) -> tuple[int, int, int, int]:
    """导入清单，返回创建、跳过、失败及封面提取失败数量。"""

    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA busy_timeout=5000")
    created = skipped = failed = cover_failed = 0
    try:
        for index, item in enumerate(manifest, 1):
            target = item["target"]
            slug = item["slug"]
            file_path = settings.UPLOAD_DIR / "books" / target
            if not file_path.is_file():
                print(f"  失败（文件不存在）: {target}")
                failed += 1
                continue
            existing = connection.execute("SELECT id FROM books WHERE slug = ?", (slug,)).fetchone()
            if existing:
                skipped += 1
                continue
            try:
                metadata = read_epub_metadata(f"books/{target}")
                title = metadata.get("title") or title_from_filename(target)
                author = metadata.get("author", "")
                description = metadata.get("description", "")
                cover_url = ""
                if not no_cover:
                    try:
                        cover_url = extract_cover_image(f"books/{target}", slug)
                    except Exception as exc:  # 单本封面异常不阻塞整批
                        cover_failed += 1
                        print(f"  警告（封面失败）: {target}: {exc}")
                connection.execute(
                    "INSERT INTO books (slug, title, author, description, cover_url, file_path) VALUES (?, ?, ?, ?, ?, ?)",
                    (slug, title, author, description, cover_url, f"/uploads/books/{target}"),
                )
                created += 1
            except Exception as exc:  # 单本异常可重试
                failed += 1
                print(f"  失败: {target}: {exc}")
            if index % max(batch_size, 1) == 0:
                connection.commit()
                print(f"  进度 {index}/{len(manifest)}（创建 {created}，跳过 {skipped}，失败 {failed}）")
        connection.commit()
    finally:
        connection.close()
    return created, skipped, failed, cover_failed


def main() -> int:
    """命令行入口。"""

    args = parse_args()
    manifest = load_manifest(args.manifest)
    print(f"读取 {len(manifest)} 条 EPUB 导入记录")
    created, skipped, failed, cover_failed = import_manifest(
        manifest, args.database, args.batch_size, args.no_cover
    )
    print(f"完成：创建 {created}，跳过 {skipped}，失败 {failed}，封面失败 {cover_failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

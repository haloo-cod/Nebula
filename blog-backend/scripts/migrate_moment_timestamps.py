"""将说说和评论 JSON 时间戳按毫秒 ID 统一为 UTC。"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock

from app.config import settings


def timestamp_from_id(record_id: object) -> str | None:
    """仅接受合理的毫秒 Unix 时间戳 ID，返回秒精度 UTC ISO 字符串。"""
    if not isinstance(record_id, int) or isinstance(record_id, bool) or not 1_000_000_000_000 <= record_id < 10_000_000_000_000:
        return None
    try:
        return datetime.fromtimestamp(record_id / 1000, timezone.utc).isoformat(timespec="seconds")
    except (OverflowError, OSError, ValueError):
        return None


def normalize_records(records: list[dict]) -> tuple[list[dict], int, int]:
    """修正说说及评论日期，保留其他字段和数组顺序。"""
    normalized = []
    changed = 0
    skipped = 0
    for source in records:
        record = dict(source)
        expected = timestamp_from_id(record.get("id"))
        if expected is None:
            skipped += 1
        elif record.get("date") != expected:
            record["date"] = expected
            changed += 1
        comments = record.get("comments")
        if isinstance(comments, list):
            fixed_comments = []
            for source_comment in comments:
                if not isinstance(source_comment, dict):
                    fixed_comments.append(source_comment)
                    continue
                comment = dict(source_comment)
                expected_comment = timestamp_from_id(comment.get("id"))
                if expected_comment is None:
                    skipped += 1
                elif comment.get("date") != expected_comment:
                    comment["date"] = expected_comment
                    changed += 1
                fixed_comments.append(comment)
            record["comments"] = fixed_comments
        normalized.append(record)
    return normalized, changed, skipped


def migrate(path: Path, apply: bool = False) -> tuple[int, int, Path | None]:
    """预览或原子迁移 JSON，应用时先备份原始字节并持有文件锁。"""
    lock = FileLock(str(path.with_suffix(path.suffix + ".lock")))
    with lock:
        original_bytes = path.read_bytes()
        data = json.loads(original_bytes)
        if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
            raise ValueError("moments.json 顶层必须是 JSON 对象数组")
        normalized, changed, skipped = normalize_records(data)
        if not apply or changed == 0:
            return changed, skipped, None

        backup = path.with_name(f"{path.name}.bak-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
        if backup.exists():
            raise FileExistsError(f"备份文件已存在: {backup}")
        shutil.copy2(path, backup)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
                json.dump(normalized, output, ensure_ascii=False, indent=2)
                output.write("\n")
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
        return changed, skipped, backup


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, help="moments.json 路径；默认读取后端 DATA_DIR")
    parser.add_argument("--apply", action="store_true", help="备份后原子写入修正")
    args = parser.parse_args()
    path = args.file or (settings.DATA_DIR / "moments.json")
    changed, skipped, backup = migrate(path, args.apply)
    mode = "applied" if args.apply else "preview"
    print(f"mode={mode} changed_dates={changed} skipped_invalid_ids={skipped}")
    if backup:
        print(f"backup={backup}")
    if not args.apply:
        print("未写入数据；检查预览后追加 --apply 才会修改文件。")


if __name__ == "__main__":
    main()

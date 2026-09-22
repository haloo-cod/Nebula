"""
Cloudflare R2 对象存储客户端（使用 S3 兼容 API）
"""
import io
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.config import settings

# 不可变对象键（含 uuid/hash 文件名）的统一浏览器缓存策略。
# 键名永不复用 → 内容变化必然换键 → 可以放心用长 max-age。
R2_CACHE_CONTROL = "public, max-age=31536000, immutable"


class R2Storage:
    """R2 存储客户端"""

    def __init__(self):
        if not settings.R2_ENABLED:
            raise RuntimeError("R2 未启用，请检查配置")

        self.endpoint = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
        self.bucket = settings.R2_BUCKET_NAME

    async def upload_file(self, key: str, file: UploadFile, content_type: str | None = None) -> int:
        """
        上传文件到 R2
        返回文件大小（bytes）
        """
        content = await file.read()
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType=content_type or file.content_type or "application/octet-stream",
            CacheControl=R2_CACHE_CONTROL,
        )
        return len(content)

    def upload_local_file(self, key: str, local_path: Path, content_type: str | None = None) -> int:
        """
        从本地文件上传到 R2
        返回文件大小
        """
        file_size = local_path.stat().st_size
        extra_args: dict = {"CacheControl": R2_CACHE_CONTROL}
        if content_type:
            extra_args["ContentType"] = content_type

        self.client.upload_file(str(local_path), self.bucket, key, ExtraArgs=extra_args)
        return file_size

    def download_stream(self, key: str) -> BinaryIO:
        """
        从 R2 流式下载文件
        返回 BytesIO 对象
        """
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return io.BytesIO(response["Body"].read())

    def delete_file(self, key: str) -> bool:
        """删除 R2 文件"""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def get_public_url(self, key: str) -> str:
        """
        获取文件的公开访问 URL
        优先使用自定义域名，否则使用默认 R2 域名
        """
        if settings.R2_PUBLIC_DOMAIN:
            return f"{settings.R2_PUBLIC_DOMAIN.rstrip('/')}/{key}"
        return f"{self.endpoint}/{self.bucket}/{key}"

    def file_exists(self, key: str) -> bool:
        """检查文件是否存在"""
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def presign_put(
        self,
        key: str,
        content_type: str | None = None,
        expires_in: int = 3600,
        cache_control: str | None = None,
    ) -> str:
        """生成预签名 PUT URL，供浏览器不经服务器直传 R2。

        需要 CORS 允许浏览器发起 PUT（R2 控制台或 S3 API 配置）。
        cache_control 参与签名：浏览器 PUT 时必须回传同值的 Cache-Control 头。
        """
        params: dict = {"Bucket": self.bucket, "Key": key}
        if content_type:
            params["ContentType"] = content_type
        if cache_control:
            params["CacheControl"] = cache_control
        return self.client.generate_presigned_url(
            "put_object",
            Params=params,
            ExpiresIn=expires_in,
        )

    def copy_cache_metadata(self, key: str) -> bool:
        """为存量对象补写 Cache-Control 元数据（服务端自复制）。

        用 copy_source=key 复制到自身并替换元数据；新对象键名不变、
        ETag/Last-Modified 会变化，内容不变。对象不存在时返回 False。
        """
        try:
            self.client.copy_object(
                Bucket=self.bucket,
                Key=key,
                CopySource={"Bucket": self.bucket, "Key": key},
                MetadataDirective="REPLACE",
                CacheControl=R2_CACHE_CONTROL,
            )
            return True
        except ClientError:
            return False


# 全局单例
_r2_client: R2Storage | None = None


def get_r2_client() -> R2Storage:
    """获取 R2 客户端单例"""
    global _r2_client
    if _r2_client is None:
        _r2_client = R2Storage()
    return _r2_client

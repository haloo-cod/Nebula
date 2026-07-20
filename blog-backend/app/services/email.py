"""可选 SMTP 邮件服务。"""

import asyncio
import smtplib
from email.message import EmailMessage

from app.config import settings


async def send_verification_email(recipient: str, verification_url: str) -> None:
    """发送邮箱验证链接；未配置 SMTP 时在开发日志输出链接。"""

    if not settings.SMTP_HOST:
        print(f"[email] Verify {recipient}: {verification_url}")
        return
    message = EmailMessage()
    message["Subject"] = "验证你的 Starlit Blog 账户"
    message["From"] = settings.SMTP_FROM or settings.SMTP_USERNAME
    message["To"] = recipient
    message.set_content(f"请在 24 小时内访问以下链接完成邮箱验证：\n\n{verification_url}")

    def send() -> None:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as client:
            if settings.SMTP_USE_TLS:
                client.starttls()
            if settings.SMTP_USERNAME:
                client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            client.send_message(message)

    await asyncio.to_thread(send)

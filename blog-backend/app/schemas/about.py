"""关于页相关 Pydantic schemas。"""

from pydantic import BaseModel


class AboutContent(BaseModel):
    """关于页 Markdown 内容。"""

    content_md: str

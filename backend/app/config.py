"""运行配置：端口、跨域、运行环境。"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    app_name: str = "巡更工坊 · 源站变更轮询与差异抽取平台"
    env: str = "local"
    port: int = 8009
    allowed_origins: list[str] = field(
        default_factory=lambda: [
            "http://127.0.0.1:5182",
            "http://localhost:5182",
        ]
    )
    page_size_default: int = 20
    page_size_max: int = 200


settings = Settings()

"""站点登记·注册管理，产出站点条目数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class SiteRegistryService(BaseModuleService):
    MODULE = "site_registry"
    ENTITY = "站点条目"
    OPERATION_TERM = "接入"
    LIST_FIELDS = ["站点编号", "站点名称", "站点类别", "接入状态", "历史变更率", "登记时间", "最近轮询"]
    REQUIRED_FIELDS = ["站点编号", "站点名称", "站点类别"]
    STATUS_ORDER = ["已登记", "验证中", "已验证", "已下线"]
    ACTION_RULES = {"提交验证": "验证中", "确认验证": "已验证", "下线站点": "已下线"}
    NEGATIVE_ACTIONS = ["下线站点"]

    def verified_sites(self) -> list[dict[str, Any]]:
        """获取全部已验证站点。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已验证"]

    def sites_by_category(self, category: str) -> list[dict[str, Any]]:
        """按站点类别过滤。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("站点类别") == category]

    def high_change_rate_sites(self, min_rate: float = 30.0) -> list[dict[str, Any]]:
        """获取历史变更率超过阈值的站点。"""
        rows = store.rows(self.MODULE)
        result: list[dict[str, Any]] = []
        for r in rows:
            try:
                rate = float(r.get("历史变更率", "0"))
            except (ValueError, TypeError):
                rate = 0.0
            if rate >= min_rate:
                result.append(r)
        return result

    def inactive_sites(self) -> list[dict[str, Any]]:
        """获取已下线的站点。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已下线"]
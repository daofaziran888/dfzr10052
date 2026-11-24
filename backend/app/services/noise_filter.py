"""噪声过滤·规则管理，产出过滤记录数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class NoiseFilterService(BaseModuleService):
    MODULE = "noise_filter"
    ENTITY = "过滤记录"
    OPERATION_TERM = "去重"
    LIST_FIELDS = ["过滤编号", "检测编号", "过滤规则", "被滤条数", "保留条数", "过滤时间"]
    REQUIRED_FIELDS = ["过滤编号", "检测编号", "过滤规则"]
    STATUS_ORDER = ["过滤中", "待复核", "已确认", "规则失效"]
    ACTION_RULES = {"提交复核": "待复核", "确认过滤": "已确认", "失效规则": "规则失效"}
    NEGATIVE_ACTIONS = ["失效规则"]

    def full_noise_results(self) -> list[dict[str, Any]]:
        """获取全过滤（无保留条数）的噪声记录。"""
        rows = store.rows(self.MODULE)
        result: list[dict[str, Any]] = []
        for r in rows:
            retain = r.get("保留条数", "0")
            try:
                retained = int(retain)
            except (ValueError, TypeError):
                retained = 0
            if retained == 0:
                result.append(r)
        return result

    def filtering_effectiveness(self) -> dict[str, float]:
        """计算过滤有效性：被滤条数占总差异的比率。"""
        rows = store.rows(self.MODULE)
        total_filtered = 0
        total_retained = 0
        for r in rows:
            try:
                total_filtered += int(r.get("被滤条数", "0"))
                total_retained += int(r.get("保留条数", "0"))
            except (ValueError, TypeError):
                pass
        total = total_filtered + total_retained
        rate = round(total_filtered / max(total, 1), 2)
        return {"filtered": total_filtered, "retained": total_retained, "filter_rate": rate}

    def rules_with_invalid_status(self) -> list[dict[str, Any]]:
        """获取已失效的过滤规则。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "规则失效"]
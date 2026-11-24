"""回放对比·稳定性验证，产出对比记录数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class ReplayCompareService(BaseModuleService):
    MODULE = "replay_compare"
    ENTITY = "对比记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["对比编号", "计划编号", "原事件条数", "重放事件条数", "差异条数", "对比时间"]
    REQUIRED_FIELDS = ["对比编号", "计划编号"]
    STATUS_ORDER = ["重放中", "待对比", "已对比", "差异待判"]
    ACTION_RULES = {"提交对比": "待对比", "确认对比": "已对比", "登记待判": "差异待判"}
    NEGATIVE_ACTIONS = ["登记待判"]

    DIFF_COUNT_THRESHOLD = 2

    def unstable_compares(self) -> list[dict[str, Any]]:
        """获取差异条数超标的对比记录。"""
        rows = store.rows(self.MODULE)
        result: list[dict[str, Any]] = []
        for r in rows:
            try:
                diff = int(r.get("差异条数", "0"))
            except (ValueError, TypeError):
                diff = 0
            if diff > self.DIFF_COUNT_THRESHOLD:
                result.append(r)
        return result

    def compare_diff_rate(self) -> float:
        """计算整体差异率：差异条数总和/原事件条数总和。"""
        rows = store.rows(self.MODULE)
        total_orig = 0
        total_diff = 0
        for r in rows:
            try:
                total_orig += int(r.get("原事件条数", "0"))
                total_diff += int(r.get("差异条数", "0"))
            except (ValueError, TypeError):
                pass
        return round(total_diff / max(total_orig, 1), 2)

    def pending_compares(self) -> list[dict[str, Any]]:
        """获取待对比的记录。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") in ("待对比", "差异待判")]

    def stable_compares(self) -> list[dict[str, Any]]:
        """获取已确认一致的对比记录。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已对比"]
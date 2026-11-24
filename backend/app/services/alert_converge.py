"""告警收敛·风暴防护，产出收敛记录数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class AlertConvergeService(BaseModuleService):
    MODULE = "alert_converge"
    ENTITY = "收敛记录"
    OPERATION_TERM = "归并"
    LIST_FIELDS = ["收敛编号", "告警来源", "收敛窗口", "原始条数", "合并条数", "收敛时间"]
    REQUIRED_FIELDS = ["收敛编号", "告警来源", "收敛窗口"]
    STATUS_ORDER = ["收敛中", "待确认", "已确认", "已下发"]
    ACTION_RULES = {"提交确认": "待确认", "确认收敛": "已确认", "下发告警": "已下发"}
    NEGATIVE_ACTIONS = []

    def confirmed_converges(self) -> list[dict[str, Any]]:
        """获取已确认的收敛记录。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已确认"]

    def dispatched_alerts(self) -> list[dict[str, Any]]:
        """获取已下发的收敛告警。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已下发"]

    def convergence_rate_by_source(self) -> dict[str, float]:
        """按来源计算收敛率（合并条数/原始条数）。"""
        rows = store.rows(self.MODULE)
        result: dict[str, list[int]] = {}
        for r in rows:
            source = r.get("告警来源", "未归集")
            if source not in result:
                result[source] = [0, 0]
            try:
                result[source][0] += int(r.get("原始条数", "0"))
                result[source][1] += int(r.get("合并条数", "0"))
            except (ValueError, TypeError):
                pass
        return {
            src: round(merged / max(raw, 1), 2)
            for src, (raw, merged) in result.items()
        }

    def sources_exceeding_threshold(self, max_raw: int = 10) -> list[dict[str, Any]]:
        """获取原始条数超过阈值的收敛记录。"""
        rows = store.rows(self.MODULE)
        result: list[dict[str, Any]] = []
        for r in rows:
            try:
                raw = int(r.get("原始条数", "0"))
            except (ValueError, TypeError):
                raw = 0
            if raw > max_raw:
                result.append(r)
        return result
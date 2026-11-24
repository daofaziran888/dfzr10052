"""抽取指标·日报汇总，产出指标快照数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class ExtractMetricsService(BaseModuleService):
    MODULE = "extract_metrics"
    ENTITY = "指标快照"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["快照编号", "统计日期", "轮询成功率", "变更检出率", "推送及时率", "快照时间"]
    REQUIRED_FIELDS = ["快照编号", "统计日期"]
    STATUS_ORDER = ["已生成", "待复核", "已复核", "已发布"]
    ACTION_RULES = {"提交复核": "待复核", "确认复核": "已复核", "发布快照": "已发布"}
    NEGATIVE_ACTIONS = []

    def metrics_for_date(self, date_str: str) -> dict[str, Any] | None:
        """获取某日期的指标快照。"""
        rows = store.rows(self.MODULE)
        for r in rows:
            if r.get("统计日期") == date_str:
                return r
        return None

    def published_metrics(self) -> list[dict[str, Any]]:
        """获取已发布的指标快照。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已发布"]

    def latest_metrics_trend(self) -> dict[str, list[float]]:
        """获取指标趋势数据。"""
        rows = store.rows(self.MODULE)
        result: dict[str, list[float]] = {
            "poll_success": [],
            "change_detect": [],
            "push_timeliness": [],
        }
        sorted_rows = sorted(rows, key=lambda r: r.get("统计日期", ""))
        for r in sorted_rows:
            try:
                result["poll_success"].append(float(r.get("轮询成功率", "0")))
                result["change_detect"].append(float(r.get("变更检出率", "0")))
                result["push_timeliness"].append(float(r.get("推送及时率", "0")))
            except (ValueError, TypeError):
                pass
        return result

    def rate_below_threshold(self, field: str, threshold: float) -> list[dict[str, Any]]:
        """获取某指标低于阈值的快照日期。"""
        rows = store.rows(self.MODULE)
        result: list[dict[str, Any]] = []
        for r in rows:
            try:
                val = float(r.get(field, "0"))
            except (ValueError, TypeError):
                val = 0.0
            if val < threshold:
                result.append(r)
        return result
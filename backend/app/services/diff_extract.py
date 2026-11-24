"""差异解析·字段级差异管理，产出差异块数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class DiffExtractService(BaseModuleService):
    MODULE = "diff_extract"
    ENTITY = "差异块"
    OPERATION_TERM = "解析"
    LIST_FIELDS = ["差异编号", "检测编号", "差异类型", "差异位置", "抽取字段数", "置信度", "抽取时间"]
    REQUIRED_FIELDS = ["差异编号", "检测编号", "差异类型"]
    STATUS_ORDER = ["抽取中", "待复核", "已确认", "已作废"]
    ACTION_RULES = {"提交复核": "待复核", "确认差异": "已确认", "作废差异": "已作废"}
    NEGATIVE_ACTIONS = ["作废差异"]

    CONFIDENCE_THRESHOLD = 0.7

    def high_confidence_diffs(self, min_confidence: float | None = None) -> list[dict[str, Any]]:
        """获取高置信度差异块。"""
        th = min_confidence or self.CONFIDENCE_THRESHOLD
        rows = store.rows(self.MODULE)
        result: list[dict[str, Any]] = []
        for r in rows:
            try:
                conf = float(r.get("置信度", "0"))
            except (ValueError, TypeError):
                conf = 0.0
            if conf >= th:
                result.append(r)
        return result

    def diffs_for_detection(self, detect_id: str) -> list[dict[str, Any]]:
        """获取某次检测的全部差异块。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("检测编号") == detect_id]

    def diff_type_distribution(self) -> dict[str, int]:
        """按差异类型统计。"""
        rows = store.rows(self.MODULE)
        dist: dict[str, int] = {}
        for r in rows:
            dt = r.get("差异类型", "未知")
            dist[dt] = dist.get(dt, 0) + 1
        return dist

    def invalidate_diffs_for_detection(self, detect_id: str) -> int:
        """将某次检测的全部差异块作废。"""
        rows = store.rows(self.MODULE)
        count = 0
        for r in rows:
            if r.get("检测编号") == detect_id and r.get("status") in ("待复核", "已确认"):
                r["status"] = "已作废"
                r["abnormal"] = True
                count += 1
        return count
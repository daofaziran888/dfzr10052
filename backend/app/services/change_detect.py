"""变更检测·判定管理，产出检测结果数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class ChangeDetectService(BaseModuleService):
    MODULE = "change_detect"
    ENTITY = "检测结果"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["检测编号", "快照编号", "前序快照", "相似度得分", "变化得分", "检测结论", "检测时间"]
    REQUIRED_FIELDS = ["检测编号", "快照编号", "前序快照"]
    STATUS_ORDER = ["检测中", "待判定", "已判定", "误报关闭"]
    ACTION_RULES = {"提交判定": "待判定", "确认变更": "已判定", "关闭误报": "误报关闭"}
    NEGATIVE_ACTIONS = []

    CHANGE_SCORE_THRESHOLD = 0.5

    def pending_detections(self) -> list[dict[str, Any]]:
        """获取全部待判定检测结果。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "待判定"]

    def detections_above_threshold(self, threshold: float | None = None) -> list[dict[str, Any]]:
        """获取变化得分超过阈值的检测结果。"""
        th = threshold or self.CHANGE_SCORE_THRESHOLD
        rows = store.rows(self.MODULE)
        result: list[dict[str, Any]] = []
        for r in rows:
            try:
                score = float(r.get("变化得分", "0"))
            except (ValueError, TypeError):
                score = 0.0
            if score >= th:
                result.append(r)
        return result

    def false_positive_rate(self) -> float:
        """计算误报率。"""
        rows = store.rows(self.MODULE)
        total = max(len(rows), 1)
        false_pos = sum(1 for r in rows if r.get("status") == "误报关闭")
        return round(false_pos / total, 2)

    def conclusion_distribution(self) -> dict[str, int]:
        """统计检测结论分布。"""
        rows = store.rows(self.MODULE)
        dist: dict[str, int] = {}
        for r in rows:
            conclusion = r.get("检测结论", "未知")
            dist[conclusion] = dist.get(conclusion, 0) + 1
        return dist
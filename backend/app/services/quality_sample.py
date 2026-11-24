"""质量抽样·质检管理，产出抽样单数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class QualitySampleService(BaseModuleService):
    MODULE = "quality_sample"
    ENTITY = "抽样单"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["抽样编号", "批次编号", "抽样条数", "差错条数", "抽样通过率", "评审时间"]
    REQUIRED_FIELDS = ["抽样编号", "批次编号", "抽样条数"]
    STATUS_ORDER = ["抽样中", "待评审", "已通过", "需返工"]
    ACTION_RULES = {"提交评审": "待评审", "通过批次": "已通过", "返工批次": "需返工"}
    NEGATIVE_ACTIONS = ["返工批次"]

    PASS_RATE_THRESHOLD = 0.80

    def passed_samples(self) -> list[dict[str, Any]]:
        """获取已通过的抽样单。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已通过"]

    def rework_samples(self) -> list[dict[str, Any]]:
        """获取需返工的抽样单。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "需返工"]

    def samples_below_threshold(self, threshold: float | None = None) -> list[dict[str, Any]]:
        """获取通过率低于阈值的抽样单。"""
        th = threshold or self.PASS_RATE_THRESHOLD
        rows = store.rows(self.MODULE)
        result: list[dict[str, Any]] = []
        for r in rows:
            try:
                rate = float(r.get("抽样通过率", "0"))
            except (ValueError, TypeError):
                rate = 0.0
            if rate < th:
                result.append(r)
        return result

    def average_pass_rate(self) -> float:
        """计算平均通过率。"""
        rows = store.rows(self.MODULE)
        if not rows:
            return 1.0
        total = 0.0
        for r in rows:
            try:
                total += float(r.get("抽样通过率", "0"))
            except (ValueError, TypeError):
                pass
        return round(total / len(rows), 2)
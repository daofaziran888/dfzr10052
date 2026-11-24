"""抽取批次·窗口管理，产出批次记录数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class ExtractBatchService(BaseModuleService):
    MODULE = "extract_batch"
    ENTITY = "批次记录"
    OPERATION_TERM = "聚合"
    LIST_FIELDS = ["批次编号", "计划编号", "窗口起点", "窗口终点", "事件条数", "完成时间"]
    REQUIRED_FIELDS = ["批次编号", "计划编号", "窗口起点"]
    STATUS_ORDER = ["开窗中", "待封窗", "已封窗", "已作废"]
    ACTION_RULES = {"提交封窗": "待封窗", "确认封窗": "已封窗", "作废批次": "已作废"}
    NEGATIVE_ACTIONS = ["作废批次"]

    def open_batches(self) -> list[dict[str, Any]]:
        """获取全部开窗中的批次。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "开窗中"]

    def sealed_batches_since(self, window_start: str) -> list[dict[str, Any]]:
        """获取某时间点之后封窗的批次。"""
        rows = store.rows(self.MODULE)
        return [
            r for r in rows
            if r.get("status") == "已封窗"
            and (r.get("窗口终点", "0") >= window_start)
        ]

    def total_event_count(self) -> int:
        """计算所有批次的事件条数总和。"""
        rows = store.rows(self.MODULE)
        total = 0
        for r in rows:
            try:
                total += int(r.get("事件条数", "0"))
            except (ValueError, TypeError):
                pass
        return total

    def seal_all_open_batches(self) -> int:
        """将所有开窗中批次批量封窗。"""
        rows = store.rows(self.MODULE)
        count = 0
        for r in rows:
            if r.get("status") == "开窗中":
                r["status"] = "已封窗"
                r["pending"] = False
                count += 1
        return count
"""任务派发·执行跟踪，产出派发记录数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class TaskDispatchService(BaseModuleService):
    MODULE = "task_dispatch"
    ENTITY = "派发记录"
    OPERATION_TERM = "调度"
    LIST_FIELDS = ["派发编号", "计划编号", "节点编号", "派发时间", "执行时长", "派发结果"]
    REQUIRED_FIELDS = ["派发编号", "计划编号", "节点编号"]
    STATUS_ORDER = ["待派发", "执行中", "已完成", "派发失败"]
    ACTION_RULES = {"发起派发": "执行中", "确认完成": "已完成", "登记失败": "派发失败"}
    NEGATIVE_ACTIONS = ["登记失败"]

    def executing_dispatches(self) -> list[dict[str, Any]]:
        """获取执行中的派发记录。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "执行中"]

    def failed_dispatches(self) -> list[dict[str, Any]]:
        """获取全部派发失败的记录。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "派发失败"]

    def dispatches_for_node(self, node_no: str) -> list[dict[str, Any]]:
        """获取某节点的派发记录。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("节点编号") == node_no]

    def retry_failed_dispatches(self) -> int:
        """将失败派发重置为待派发。"""
        rows = store.rows(self.MODULE)
        count = 0
        for r in rows:
            if r.get("status") == "派发失败":
                r["status"] = "待派发"
                r["pending"] = True
                count += 1
        return count
"""工作节点·状态管理，产出节点条目数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class PollWorkerService(BaseModuleService):
    MODULE = "poll_worker"
    ENTITY = "节点条目"
    OPERATION_TERM = "调度"
    LIST_FIELDS = ["节点编号", "节点地址", "负载上限", "当前任务数", "心跳时间", "节点状态"]
    REQUIRED_FIELDS = ["节点编号", "节点地址", "负载上限"]
    STATUS_ORDER = ["在线", "繁忙", "心跳超时", "已下线"]
    ACTION_RULES = {"标记繁忙": "繁忙", "判定超时": "心跳超时", "下线节点": "已下线"}
    NEGATIVE_ACTIONS = ["判定超时", "下线节点"]

    def online_nodes(self) -> list[dict[str, Any]]:
        """获取全部在线节点。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "在线"]

    def heartbeat_timeout_nodes(self) -> list[dict[str, Any]]:
        """获取心跳超时的节点。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "心跳超时"]

    def busiest_node(self) -> dict[str, Any] | None:
        """找出当前任务数最多的节点。"""
        rows = store.rows(self.MODULE)
        best = None
        best_tasks = -1
        for r in rows:
            try:
                tasks = int(r.get("当前任务数", "0"))
            except (ValueError, TypeError):
                tasks = 0
            if tasks > best_tasks:
                best_tasks = tasks
                best = r
        return best

    def capacity_remaining(self, node_id: str) -> int:
        """计算节点剩余容量。"""
        rows = store.rows(self.MODULE)
        for r in rows:
            if r.get("节点编号") == node_id:
                try:
                    cap = int(r.get("负载上限", "0"))
                    tasks = int(r.get("当前任务数", "0"))
                except (ValueError, TypeError):
                    return 0
                return max(0, cap - tasks)
        return 0
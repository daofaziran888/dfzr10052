"""变更事件·级别管理，产出事件记录数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class ChangeEventService(BaseModuleService):
    MODULE = "change_event"
    ENTITY = "事件记录"
    OPERATION_TERM = "转换"
    LIST_FIELDS = ["事件编号", "差异编号", "事件级别", "事件摘要", "发生时间", "推送状态"]
    REQUIRED_FIELDS = ["事件编号", "差异编号", "事件级别"]
    STATUS_ORDER = ["已生成", "待推送", "已推送", "推送失败"]
    ACTION_RULES = {"发起推送": "待推送", "确认推送": "已推送", "登记失败": "推送失败"}
    NEGATIVE_ACTIONS = []

    def pending_push_events(self) -> list[dict[str, Any]]:
        """获取待推送事件。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("推送状态") == "待推送"]

    def events_by_level(self, level: str) -> list[dict[str, Any]]:
        """按事件级别过滤。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("事件级别") == level]

    def failed_push_events(self) -> list[dict[str, Any]]:
        """获取推送失败事件。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("推送状态") == "推送失败"]

    def retry_failed_event(self, event_id: str) -> tuple[bool, str]:
        """重试推送失败事件。"""
        rows = store.rows(self.MODULE)
        for r in rows:
            if r.get("事件编号") == event_id:
                if r.get("推送状态") == "推送失败":
                    r["推送状态"] = "待推送"
                    r["status"] = "待推送"
                    r["pending"] = True
                    return True, f"事件 {event_id} 已重置为待推送"
                return False, f"事件 {event_id} 不处于推送失败状态"
        return False, f"事件 {event_id} 不存在"

    def event_level_distribution(self) -> dict[str, int]:
        """按事件级别统计分布。"""
        rows = store.rows(self.MODULE)
        dist: dict[str, int] = {}
        for r in rows:
            level = r.get("事件级别", "未知")
            dist[level] = dist.get(level, 0) + 1
        return dist
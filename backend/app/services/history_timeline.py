"""历史时间线·溯源管理，产出时间线条目数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class HistoryTimelineService(BaseModuleService):
    MODULE = "history_timeline"
    ENTITY = "时间线条目"
    OPERATION_TERM = "查询"
    LIST_FIELDS = ["时间线编号", "站点编号", "快照序号", "变化标记", "时间点", "溯源状态"]
    REQUIRED_FIELDS = ["时间线编号", "站点编号", "快照序号"]
    STATUS_ORDER = ["已记录", "待溯源", "已溯源", "存疑中"]
    ACTION_RULES = {"发起溯源": "待溯源", "确认溯源": "已溯源", "登记存疑": "存疑中"}
    NEGATIVE_ACTIONS = ["登记存疑"]

    def timeline_for_site(self, site_no: str) -> list[dict[str, Any]]:
        """获取某站点的完整时间线条目（按快照序号排序）。"""
        rows = store.rows(self.MODULE)
        site_rows = [r for r in rows if r.get("站点编号") == site_no]
        site_rows.sort(key=lambda r: int(r.get("快照序号", "0")))
        return site_rows

    def entries_with_changes(self) -> list[dict[str, Any]]:
        """获取标记有变更的时间线条目。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("变化标记") == "有变更"]

    def unresolved_traces(self) -> list[dict[str, Any]]:
        """获取尚未溯源的条目。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("溯源状态") == "待溯源"]

    def doubtful_entries(self) -> list[dict[str, Any]]:
        """获取存疑条目。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("溯源状态") == "存疑中"]
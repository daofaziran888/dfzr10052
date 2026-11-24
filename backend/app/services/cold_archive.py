"""冷归档·快照治理，产出归档快照数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class ColdArchiveService(BaseModuleService):
    MODULE = "cold_archive"
    ENTITY = "归档快照"
    OPERATION_TERM = "归档"
    LIST_FIELDS = ["归档编号", "快照编号", "归档层级", "归档时间", "保留天数", "可回取标记"]
    REQUIRED_FIELDS = ["归档编号", "快照编号", "归档层级"]
    STATUS_ORDER = ["待归档", "归档中", "已归档", "已销毁"]
    ACTION_RULES = {"发起归档": "归档中", "确认归档": "已归档", "销毁归档": "已销毁"}
    NEGATIVE_ACTIONS = ["销毁归档"]

    def archived_snapshots(self) -> list[dict[str, Any]]:
        """获取已归档的快照。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已归档"]

    def retrievable_archives(self) -> list[dict[str, Any]]:
        """获取可回取的归档快照。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("可回取标记") == "是"]

    def archiving_in_progress(self) -> list[dict[str, Any]]:
        """获取归档中的快照。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "归档中"]

    def destroyed_count(self) -> int:
        """获取已销毁的归档快照数。"""
        rows = store.rows(self.MODULE)
        return sum(1 for r in rows if r.get("status") == "已销毁")
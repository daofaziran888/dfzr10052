"""事件去重·指纹管理，产出去重记录数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class EventDedupService(BaseModuleService):
    MODULE = "event_dedup"
    ENTITY = "去重记录"
    OPERATION_TERM = "去重"
    LIST_FIELDS = ["去重编号", "事件编号", "重复指纹", "命中批次", "去重结论", "去重时间"]
    REQUIRED_FIELDS = ["去重编号", "事件编号", "重复指纹"]
    STATUS_ORDER = ["已标记", "复核中", "已去重", "已保留"]
    ACTION_RULES = {"提交复核": "复核中", "确认去重": "已去重", "保留事件": "已保留"}
    NEGATIVE_ACTIONS = []

    def deduplicated_events(self) -> list[dict[str, Any]]:
        """获取已被去重的记录。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("去重结论") == "已去重"]

    def retained_events(self) -> list[dict[str, Any]]:
        """获取已保留的事件。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("去重结论") == "已保留"]

    def duplicate_fingerprints(self) -> list[tuple[str, int]]:
        """查找出现多次的重复指纹。"""
        rows = store.rows(self.MODULE)
        counter: dict[str, int] = {}
        for r in rows:
            fp = r.get("重复指纹", "")
            counter[fp] = counter.get(fp, 0) + 1
        return [(fp, cnt) for fp, cnt in counter.items() if cnt > 1]

    def deduplicate_by_fingerprint(self, fingerprint: str) -> int:
        """将某指纹的重复事件标记为已去重（保留最早一条）。"""
        rows = store.rows(self.MODULE)
        matching = [r for r in rows if r.get("重复指纹") == fingerprint]
        matching.sort(key=lambda r: r.get("id", 0))
        count = 0
        for r in matching[1:]:
            if r.get("去重结论") != "已去重":
                r["去重结论"] = "已去重"
                r["status"] = "已去重"
                r["pending"] = False
                count += 1
        return count
"""快照存储·版本管理，产出站点快照数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class SnapshotStoreService(BaseModuleService):
    MODULE = "snapshot_store"
    ENTITY = "站点快照"
    OPERATION_TERM = "抓取"
    LIST_FIELDS = ["快照编号", "计划编号", "抓取时间", "内容指纹", "快照大小", "存储分区", "版本序号"]
    REQUIRED_FIELDS = ["快照编号", "计划编号", "抓取时间"]
    STATUS_ORDER = ["写入中", "待校验", "已入库", "已过期"]
    ACTION_RULES = {"提交校验": "待校验", "确认入库": "已入库", "标记过期": "已过期"}
    NEGATIVE_ACTIONS = []

    def latest_snapshot_for_plan(self, plan_no: str) -> dict[str, Any] | None:
        """获取某计划最新版本快照。"""
        rows = store.rows(self.MODULE)
        plan_snaps = [r for r in rows if r.get("计划编号") == plan_no]
        if not plan_snaps:
            return None
        return max(plan_snaps, key=lambda r: int(r.get("版本序号", "0")))

    def fingerprint_duplicates(self, fingerprint: str) -> list[dict[str, Any]]:
        """按内容指纹查找重复快照。"""
        rows = store.rows(self.MODULE)
        return [
            r for r in rows
            if r.get("内容指纹") == fingerprint
        ]

    def expired_snapshots(self) -> list[dict[str, Any]]:
        """获取全部已过期快照。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已过期"]

    def count_by_partition(self) -> dict[str, int]:
        """按存储分区统计快照数量。"""
        rows = store.rows(self.MODULE)
        result: dict[str, int] = {}
        for r in rows:
            part = r.get("存储分区", "未知")
            result[part] = result.get(part, 0) + 1
        return result
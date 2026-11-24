"""对比报告·周期统计，产出报告条目数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class SnapshotReportService(BaseModuleService):
    MODULE = "snapshot_report"
    ENTITY = "报告条目"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["报告编号", "站点编号", "统计周期", "变化次数", "主要变化类型", "生成时间"]
    REQUIRED_FIELDS = ["报告编号", "站点编号", "统计周期"]
    STATUS_ORDER = ["生成中", "待审阅", "已发布", "已归档"]
    ACTION_RULES = {"提交审阅": "待审阅", "发布报告": "已发布", "归档报告": "已归档"}
    NEGATIVE_ACTIONS = []

    def published_reports(self) -> list[dict[str, Any]]:
        """获取已发布的对比报告。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已发布"]

    def reports_for_site(self, site_no: str) -> list[dict[str, Any]]:
        """获取某站点全部报告。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("站点编号") == site_no]

    def reports_in_period(self, period: str) -> list[dict[str, Any]]:
        """获取某统计周期的报告。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("统计周期") == period]

    def archive_old_reports(self, before_period: str) -> int:
        """将指定周期前的报告归档。"""
        rows = store.rows(self.MODULE)
        count = 0
        for r in rows:
            if r.get("统计周期", "") < before_period and r.get("status") != "已归档":
                r["status"] = "已归档"
                r["pending"] = False
                count += 1
        return count
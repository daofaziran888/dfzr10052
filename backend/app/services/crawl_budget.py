"""抓取预算·额度管理，产出预算台账数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class CrawlBudgetService(BaseModuleService):
    MODULE = "crawl_budget"
    ENTITY = "预算台账"
    OPERATION_TERM = "抓取"
    LIST_FIELDS = ["预算编号", "站点编号", "日请求上限", "已用请求", "剩余配额", "预算周期", "更新时间"]
    REQUIRED_FIELDS = ["预算编号", "站点编号", "日请求上限"]
    STATUS_ORDER = ["计量中", "待复核", "已确认", "已超支"]
    ACTION_RULES = {"提交复核": "待复核", "确认台账": "已确认", "登记超支": "已超支"}
    NEGATIVE_ACTIONS = []

    def over_budget_sites(self) -> list[dict[str, Any]]:
        """获取已超支的站点预算。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已超支"]

    def remaining_quota_for_site(self, site_no: str) -> int:
        """查询某站点剩余配额。"""
        rows = store.rows(self.MODULE)
        for r in rows:
            if r.get("站点编号") == site_no:
                try:
                    return int(r.get("剩余配额", "0"))
                except (ValueError, TypeError):
                    return 0
        return 0

    def daily_usage_threshold_check(self, threshold_ratio: float = 0.85) -> list[dict[str, Any]]:
        """列出已用请求超过日请求上限指定比例的站点。"""
        rows = store.rows(self.MODULE)
        result: list[dict[str, Any]] = []
        for r in rows:
            try:
                limit = int(r.get("日请求上限", "1"))
                used = int(r.get("已用请求", "0"))
            except (ValueError, TypeError):
                continue
            if limit > 0 and used / limit >= threshold_ratio:
                result.append(r)
        return result

    def reset_daily_usage(self) -> int:
        """重置所有站点当日已用请求。"""
        rows = store.rows(self.MODULE)
        count = 0
        for r in rows:
            r["已用请求"] = "0"
            r["剩余配额"] = r.get("日请求上限", "0")
            r["更新时间"] = "2026-11-24"
            count += 1
        return count
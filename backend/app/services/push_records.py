"""推送台账·明细记录，产出推送明细数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class PushRecordsService(BaseModuleService):
    MODULE = "push_records"
    ENTITY = "推送明细"
    OPERATION_TERM = "查询"
    LIST_FIELDS = ["推送编号", "事件编号", "订阅编号", "推送时间", "推送结果", "重试次数"]
    REQUIRED_FIELDS = ["推送编号", "事件编号", "订阅编号"]
    STATUS_ORDER = ["待推送", "推送中", "已成功", "已失败"]
    ACTION_RULES = {"发起推送": "推送中", "确认成功": "已成功", "登记失败": "已失败"}
    NEGATIVE_ACTIONS = ["登记失败"]

    MAX_RETRIES = 3

    def successful_pushes(self) -> list[dict[str, Any]]:
        """获取已成功的推送明细。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已成功"]

    def failed_pushes(self) -> list[dict[str, Any]]:
        """获取已失败的推送明细。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已失败"]

    def pushes_need_retry(self) -> list[dict[str, Any]]:
        """获取需要重试的推送明细（失败且重试次数未超上限）。"""
        rows = store.rows(self.MODULE)
        result: list[dict[str, Any]] = []
        for r in rows:
            if r.get("status") != "已失败":
                continue
            try:
                retries = int(r.get("重试次数", "0"))
            except (ValueError, TypeError):
                retries = 0
            if retries < self.MAX_RETRIES:
                result.append(r)
        return result

    def push_timeliness_rate(self) -> float:
        """计算推送及时率：已成功/总推送。"""
        rows = store.rows(self.MODULE)
        total = len(rows)
        if total == 0:
            return 1.0
        success = sum(1 for r in rows if r.get("status") == "已成功")
        return round(success / total, 2)
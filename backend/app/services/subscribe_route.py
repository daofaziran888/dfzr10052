"""订阅路由·推送管理，产出订阅条目数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class SubscribeRouteService(BaseModuleService):
    MODULE = "subscribe_route"
    ENTITY = "订阅条目"
    OPERATION_TERM = "查询"
    LIST_FIELDS = ["订阅编号", "订阅方", "事件级别过滤", "推送通道", "创建时间"]
    REQUIRED_FIELDS = ["订阅编号", "订阅方", "推送通道"]
    STATUS_ORDER = ["草稿", "待激活", "已激活", "已退订"]
    ACTION_RULES = {"提交激活": "待激活", "激活订阅": "已激活", "退订处理": "已退订"}
    NEGATIVE_ACTIONS = []

    def active_subscriptions(self) -> list[dict[str, Any]]:
        """获取全部已激活订阅。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已激活"]

    def subscribers_by_channel(self, channel: str) -> list[dict[str, Any]]:
        """按推送通道过滤订阅方。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("推送通道") == channel]

    def subscribers_for_level(self, level: str) -> list[dict[str, Any]]:
        """获取订阅特定事件级别的订阅方。"""
        rows = store.rows(self.MODULE)
        result: list[dict[str, Any]] = []
        for r in rows:
            level_filter = r.get("事件级别过滤", "")
            if level_filter == "全部" or level_filter == level:
                result.append(r)
        return result

    def inactive_subscriptions(self) -> list[dict[str, Any]]:
        """获取已退订的订阅。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已退订"]
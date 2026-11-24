"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SubscribeRouteService(BaseModuleService):
    MODULE = "subscribe_route"
    ENTITY = "订阅条目"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["订阅编号", "订阅方", "事件级别过滤", "推送通道", "创建时间"]
    REQUIRED_FIELDS = ["订阅编号", "订阅方", "事件级别过滤"]
    STATUS_ORDER = ["草稿", "待激活", "已激活", "已退订"]
    ACTION_RULES = {"提交激活": "待激活", "激活订阅": "已激活", "退订处理": "已退订"}
    NEGATIVE_ACTIONS = []

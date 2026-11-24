"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ChangeEventService(BaseModuleService):
    MODULE = "change_event"
    ENTITY = "事件记录"
    OPERATION_TERM = "转换"
    LIST_FIELDS = ["事件编号", "差异编号", "事件级别", "事件摘要", "发生时间", "推送状态"]
    REQUIRED_FIELDS = ["事件编号", "差异编号", "事件级别"]
    STATUS_ORDER = ["已生成", "待推送", "已推送", "推送失败"]
    ACTION_RULES = {"发起推送": "待推送", "确认推送": "已推送", "登记失败": "推送失败"}
    NEGATIVE_ACTIONS = []

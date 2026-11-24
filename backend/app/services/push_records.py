"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class PushRecordsService(BaseModuleService):
    MODULE = "push_records"
    ENTITY = "推送明细"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["推送编号", "事件编号", "订阅编号", "推送时间", "推送结果", "重试次数"]
    REQUIRED_FIELDS = ["推送编号", "事件编号", "订阅编号"]
    STATUS_ORDER = ["待推送", "推送中", "已成功", "已失败"]
    ACTION_RULES = {"发起推送": "推送中", "确认成功": "已成功", "登记失败": "已失败"}
    NEGATIVE_ACTIONS = []

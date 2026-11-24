"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class EventDedupService(BaseModuleService):
    MODULE = "event_dedup"
    ENTITY = "去重记录"
    OPERATION_TERM = "抓取"
    LIST_FIELDS = ["去重编号", "事件编号", "重复指纹", "命中批次", "去重结论", "去重时间"]
    REQUIRED_FIELDS = ["去重编号", "事件编号", "重复指纹"]
    STATUS_ORDER = ["已标记", "复核中", "已去重", "已保留"]
    ACTION_RULES = {"提交复核": "复核中", "确认去重": "已去重", "保留事件": "已保留"}
    NEGATIVE_ACTIONS = []

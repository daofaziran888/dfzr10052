"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class TaskDispatchService(BaseModuleService):
    MODULE = "task_dispatch"
    ENTITY = "派发记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["派发编号", "计划编号", "节点编号", "派发时间", "执行时长", "派发结果"]
    REQUIRED_FIELDS = ["派发编号", "计划编号", "节点编号"]
    STATUS_ORDER = ["待派发", "执行中", "已完成", "派发失败"]
    ACTION_RULES = {"发起派发": "执行中", "确认完成": "已完成", "登记失败": "派发失败"}
    NEGATIVE_ACTIONS = []

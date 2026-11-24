"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ReplayCompareService(BaseModuleService):
    MODULE = "replay_compare"
    ENTITY = "对比记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["对比编号", "计划编号", "原事件条数", "重放事件条数", "差异条数", "对比时间"]
    REQUIRED_FIELDS = ["对比编号", "计划编号", "原事件条数"]
    STATUS_ORDER = ["重放中", "待对比", "已对比", "差异待判"]
    ACTION_RULES = {"提交对比": "待对比", "确认对比": "已对比", "登记待判": "差异待判"}
    NEGATIVE_ACTIONS = []

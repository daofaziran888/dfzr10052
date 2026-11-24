"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class FieldMappingService(BaseModuleService):
    MODULE = "field_mapping"
    ENTITY = "映射规则"
    OPERATION_TERM = "转换"
    LIST_FIELDS = ["规则编号", "站点编号", "源字段路径", "目标字段", "转换表达式", "规则版本", "生效时间"]
    REQUIRED_FIELDS = ["规则编号", "站点编号", "源字段路径"]
    STATUS_ORDER = ["草拟中", "待验证", "已生效", "已废弃"]
    ACTION_RULES = {"提交验证": "待验证", "生效规则": "已生效", "废弃规则": "已废弃"}
    NEGATIVE_ACTIONS = []

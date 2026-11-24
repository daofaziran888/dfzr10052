"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class NoiseFilterService(BaseModuleService):
    MODULE = "noise_filter"
    ENTITY = "过滤记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["过滤编号", "检测编号", "过滤规则", "被滤条数", "保留条数", "过滤时间"]
    REQUIRED_FIELDS = ["过滤编号", "检测编号", "过滤规则"]
    STATUS_ORDER = ["过滤中", "待复核", "已确认", "规则失效"]
    ACTION_RULES = {"提交复核": "待复核", "确认过滤": "已确认", "失效规则": "规则失效"}
    NEGATIVE_ACTIONS = []

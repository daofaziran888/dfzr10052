"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class QualitySampleService(BaseModuleService):
    MODULE = "quality_sample"
    ENTITY = "抽样单"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["抽样编号", "批次编号", "抽样条数", "差错条数", "抽样通过率", "评审时间"]
    REQUIRED_FIELDS = ["抽样编号", "批次编号", "抽样条数"]
    STATUS_ORDER = ["抽样中", "待评审", "已通过", "需返工"]
    ACTION_RULES = {"提交评审": "待评审", "通过批次": "已通过", "返工批次": "需返工"}
    NEGATIVE_ACTIONS = []

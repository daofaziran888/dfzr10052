"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class DiffExtractService(BaseModuleService):
    MODULE = "diff_extract"
    ENTITY = "差异块"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["差异编号", "检测编号", "差异类型", "差异位置", "抽取字段数", "置信度", "抽取时间"]
    REQUIRED_FIELDS = ["差异编号", "检测编号", "差异类型"]
    STATUS_ORDER = ["抽取中", "待复核", "已确认", "已作废"]
    ACTION_RULES = {"提交复核": "待复核", "确认差异": "已确认", "作废差异": "已作废"}
    NEGATIVE_ACTIONS = ["作废差异"]

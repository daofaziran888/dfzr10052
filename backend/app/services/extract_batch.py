"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ExtractBatchService(BaseModuleService):
    MODULE = "extract_batch"
    ENTITY = "批次记录"
    OPERATION_TERM = "聚合"
    LIST_FIELDS = ["批次编号", "计划编号", "窗口起点", "窗口终点", "事件条数", "完成时间"]
    REQUIRED_FIELDS = ["批次编号", "计划编号", "窗口起点"]
    STATUS_ORDER = ["开窗中", "待封窗", "已封窗", "已作废"]
    ACTION_RULES = {"提交封窗": "待封窗", "确认封窗": "已封窗", "作废批次": "已作废"}
    NEGATIVE_ACTIONS = ["作废批次"]

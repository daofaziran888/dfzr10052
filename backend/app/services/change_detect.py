"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ChangeDetectService(BaseModuleService):
    MODULE = "change_detect"
    ENTITY = "检测结果"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["检测编号", "快照编号", "前序快照", "相似度得分", "变化得分", "检测结论", "检测时间"]
    REQUIRED_FIELDS = ["检测编号", "快照编号", "前序快照"]
    STATUS_ORDER = ["检测中", "待判定", "已判定", "误报关闭"]
    ACTION_RULES = {"提交判定": "待判定", "确认变更": "已判定", "关闭误报": "误报关闭"}
    NEGATIVE_ACTIONS = []

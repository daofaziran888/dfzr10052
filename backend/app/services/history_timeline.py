"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class HistoryTimelineService(BaseModuleService):
    MODULE = "history_timeline"
    ENTITY = "时间线条目"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["时间线编号", "站点编号", "快照序号", "变化标记", "时间点", "溯源状态"]
    REQUIRED_FIELDS = ["时间线编号", "站点编号", "快照序号"]
    STATUS_ORDER = ["已记录", "待溯源", "已溯源", "存疑中"]
    ACTION_RULES = {"发起溯源": "待溯源", "确认溯源": "已溯源", "登记存疑": "存疑中"}
    NEGATIVE_ACTIONS = []

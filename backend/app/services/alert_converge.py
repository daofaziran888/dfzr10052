"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class AlertConvergeService(BaseModuleService):
    MODULE = "alert_converge"
    ENTITY = "收敛记录"
    OPERATION_TERM = "合并"
    LIST_FIELDS = ["收敛编号", "告警来源", "收敛窗口", "原始条数", "合并条数", "收敛时间"]
    REQUIRED_FIELDS = ["收敛编号", "告警来源", "收敛窗口"]
    STATUS_ORDER = ["收敛中", "待确认", "已确认", "已下发"]
    ACTION_RULES = {"提交确认": "待确认", "确认收敛": "已确认", "下发告警": "已下发"}
    NEGATIVE_ACTIONS = []

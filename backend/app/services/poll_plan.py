"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class PollPlanService(BaseModuleService):
    MODULE = "poll_plan"
    ENTITY = "计划单"
    OPERATION_TERM = "抓取"
    LIST_FIELDS = ["计划编号", "站点编号", "轮询频率", "抓取深度", "过滤规则", "创建时间"]
    REQUIRED_FIELDS = ["计划编号", "站点编号", "轮询频率"]
    STATUS_ORDER = ["草稿", "待审核", "已生效", "已暂停"]
    ACTION_RULES = {"提交审核": "待审核", "生效计划": "已生效", "暂停计划": "已暂停"}
    NEGATIVE_ACTIONS = []

"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SnapshotReportService(BaseModuleService):
    MODULE = "snapshot_report"
    ENTITY = "报告条目"
    OPERATION_TERM = "归档"
    LIST_FIELDS = ["报告编号", "站点编号", "统计周期", "变化次数", "主要变化类型", "生成时间"]
    REQUIRED_FIELDS = ["报告编号", "站点编号", "统计周期"]
    STATUS_ORDER = ["生成中", "待审阅", "已发布", "已归档"]
    ACTION_RULES = {"提交审阅": "待审阅", "发布报告": "已发布", "归档报告": "已归档"}
    NEGATIVE_ACTIONS = []

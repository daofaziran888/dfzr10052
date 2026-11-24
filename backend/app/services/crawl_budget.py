"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class CrawlBudgetService(BaseModuleService):
    MODULE = "crawl_budget"
    ENTITY = "预算台账"
    OPERATION_TERM = "抓取"
    LIST_FIELDS = ["预算编号", "站点编号", "日请求上限", "已用请求", "剩余配额", "预算周期", "更新时间"]
    REQUIRED_FIELDS = ["预算编号", "站点编号", "日请求上限"]
    STATUS_ORDER = ["计量中", "待复核", "已确认", "已超支"]
    ACTION_RULES = {"提交复核": "待复核", "确认台账": "已确认", "登记超支": "已超支"}
    NEGATIVE_ACTIONS = []

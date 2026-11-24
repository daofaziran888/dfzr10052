"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SiteRegistryService(BaseModuleService):
    MODULE = "site_registry"
    ENTITY = "站点条目"
    OPERATION_TERM = "接入"
    LIST_FIELDS = ["站点编号", "站点名称", "站点类别", "接入状态", "历史变更率", "登记时间", "最近轮询"]
    REQUIRED_FIELDS = ["站点编号", "站点名称", "站点类别"]
    STATUS_ORDER = ["已登记", "验证中", "已验证", "已下线"]
    ACTION_RULES = {"提交验证": "验证中", "确认验证": "已验证", "下线站点": "已下线"}
    NEGATIVE_ACTIONS = ["下线站点"]

"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SnapshotStoreService(BaseModuleService):
    MODULE = "snapshot_store"
    ENTITY = "站点快照"
    OPERATION_TERM = "抓取"
    LIST_FIELDS = ["快照编号", "计划编号", "抓取时间", "内容指纹", "快照大小", "存储分区", "版本序号"]
    REQUIRED_FIELDS = ["快照编号", "计划编号", "抓取时间"]
    STATUS_ORDER = ["写入中", "待校验", "已入库", "已过期"]
    ACTION_RULES = {"提交校验": "待校验", "确认入库": "已入库", "标记过期": "已过期"}
    NEGATIVE_ACTIONS = []

"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class PollWorkerService(BaseModuleService):
    MODULE = "poll_worker"
    ENTITY = "节点条目"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["节点编号", "节点地址", "负载上限", "当前任务数", "心跳时间", "节点状态"]
    REQUIRED_FIELDS = ["节点编号", "节点地址", "负载上限"]
    STATUS_ORDER = ["在线", "繁忙", "心跳超时", "已下线"]
    ACTION_RULES = {"标记繁忙": "繁忙", "判定超时": "心跳超时", "下线节点": "已下线"}
    NEGATIVE_ACTIONS = ["下线节点"]

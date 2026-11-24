"""轮询计划·周期管理，产出计划单数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class PollPlanService(BaseModuleService):
    MODULE = "poll_plan"
    ENTITY = "计划单"
    OPERATION_TERM = "抓取"
    LIST_FIELDS = ["计划编号", "站点编号", "轮询频率", "抓取深度", "过滤规则", "创建时间"]
    REQUIRED_FIELDS = ["计划编号", "站点编号", "轮询频率"]
    STATUS_ORDER = ["草稿", "待审核", "已生效", "已暂停"]
    ACTION_RULES = {"提交审核": "待审核", "生效计划": "已生效", "暂停计划": "已暂停"}
    NEGATIVE_ACTIONS = []

    FREQUENCY_ORDER = ["高频轮询", "中频轮询", "低频轮询"]

    def get_active_plans(self) -> list[dict[str, Any]]:
        """获取全部已生效计划。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已生效"]

    def plans_by_frequency(self, frequency: str) -> list[dict[str, Any]]:
        """按轮询频率过滤计划。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("轮询频率") == frequency]

    def pending_review_count(self) -> int:
        """待审核计划计数。"""
        rows = store.rows(self.MODULE)
        return sum(1 for r in rows if r.get("status") == "待审核")

    def downgrade_frequency(self, plan_no: str) -> tuple[bool, str]:
        """降频：把计划轮询频率降至下一级。"""
        rows = store.rows(self.MODULE)
        for r in rows:
            if r.get("计划编号") == plan_no:
                current = r.get("轮询频率", "")
                freq_list = self.FREQUENCY_ORDER
                if current in freq_list:
                    idx = freq_list.index(current)
                    if idx < len(freq_list) - 1:
                        r["轮询频率"] = freq_list[idx + 1]
                        r["abnormal"] = True
                        return True, f"计划 {plan_no} 从{current}降频为{freq_list[idx + 1]}"
                return False, f"计划 {plan_no} 无法再降频"
        return False, f"计划 {plan_no} 不存在"

    def plans_for_site(self, site_no: str) -> list[dict[str, Any]]:
        """获取某站点全部轮询计划。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("站点编号") == site_no]
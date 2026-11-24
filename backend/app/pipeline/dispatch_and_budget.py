"""任务派发与预算管控 管线：轮询计划→节点派发→预算校验→执行记录。

核心行为：
- 生效计划按节点负载均衡派发到在线节点
- 派发前检查该站点当日已用请求是否超过上限
- 超支计划降频为低频轮询，记录派发失败
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.store import store


@dataclass
class DispatchResult:
    dispatch_id: str
    plan_id: str
    node_id: str
    budget_check: str
    dispatch_time: str
    status: str
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "dispatch_id": self.dispatch_id,
            "plan_id": self.plan_id,
            "node_id": self.node_id,
            "budget_check": self.budget_check,
            "dispatch_time": self.dispatch_time,
            "status": self.status,
            "reason": self.reason,
        }


class DispatchBudgetEngine:
    """任务派发与预算管控引擎。"""

    BUDGET_LIMIT_RATIO = 0.85

    def dispatch_active_plans(self) -> list[DispatchResult]:
        """把全部生效计划派发到在线节点。"""
        plans = [p for p in store.rows("poll_plan") if p.get("status") == "已生效"]
        nodes = [n for n in store.rows("poll_worker") if n.get("status") == "在线"]
        if not nodes:
            return []
        results: list[DispatchResult] = []
        dispatch_rows = store.rows("task_dispatch")
        dispatch_id_counter = max((int(r.get("id", 0)) for r in dispatch_rows), default=0) + 1

        for idx, plan in enumerate(plans):
            node = nodes[idx % len(nodes)]
            site_no = plan.get("站点编号", "")
            budget_ok, budget_msg = self._check_crawl_budget(site_no)
            plan_no = plan.get("计划编号", "")
            node_no = node.get("节点编号", "")

            if not budget_ok:
                plan["轮询频率"] = "低频轮询"
                plan["abnormal"] = True
                results.append(DispatchResult(
                    dispatch_id=f"DISP-{dispatch_id_counter:04d}",
                    plan_id=plan_no, node_id=node_no,
                    budget_check="超支", dispatch_time="2026-11-24",
                    status="派发失败", reason=budget_msg,
                ))
                dispatch_id_counter += 1
                continue

            dr = DispatchResult(
                dispatch_id=f"DISP-{dispatch_id_counter:04d}",
                plan_id=plan_no, node_id=node_no,
                budget_check="充足", dispatch_time="2026-11-24",
                status="执行中",
            )
            entry = {
                "id": dispatch_id_counter,
                "派发编号": dr.dispatch_id,
                "计划编号": plan_no,
                "节点编号": node_no,
                "派发时间": dr.dispatch_time,
                "执行时长": "0",
                "派发结果": "执行中",
                "status": "执行中",
                "pending": True,
                "abnormal": False,
            }
            dispatch_rows.append(entry)
            results.append(dr)
            dispatch_id_counter += 1

        return results

    def _check_crawl_budget(self, site_no: str) -> tuple[bool, str]:
        """检查某站点当日抓取预算是否充足。"""
        budgets = [b for b in store.rows("crawl_budget") if b.get("站点编号") == site_no]
        if not budgets:
            return True, "无预算记录，视为充足"
        budget = budgets[0]
        try:
            daily_limit = int(budget.get("日请求上限", "0"))
            used = int(budget.get("已用请求", "0"))
        except (ValueError, TypeError):
            return True, "预算数据异常，视为充足"
        if daily_limit == 0:
            return True, "日请求上限未设置"
        if used / daily_limit >= self.BUDGET_LIMIT_RATIO:
            return False, f"站点 {site_no} 已用请求 {used}/{daily_limit} 超过阈值"
        return True, f"站点 {site_no} 剩余配额 {(daily_limit - used)}"

    def record_usage(self, site_no: str, requests: int) -> bool:
        """记录节点抓取请求消耗。"""
        budgets = [b for b in store.rows("crawl_budget") if b.get("站点编号") == site_no]
        if not budgets:
            return False
        budget = budgets[0]
        try:
            current_used = int(budget.get("已用请求", "0"))
        except (ValueError, TypeError):
            current_used = 0
        budget["已用请求"] = str(current_used + requests)
        budget["剩余配额"] = str(int(budget.get("日请求上限", "0")) - current_used - requests)
        budget["更新时间"] = "2026-11-24"
        return True

    def node_health_check(self) -> list[dict[str, Any]]:
        """检查节点健康：心跳超时的任务重新派发。"""
        nodes = store.rows("poll_worker")
        unhealthy = [n for n in nodes if n.get("status") == "心跳超时"]
        return [{"node_id": n.get("节点编号"), "address": n.get("节点地址"), "action": "需重新派发"} for n in unhealthy]

    def snapshot(self) -> dict[str, Any]:
        dispatches = store.rows("task_dispatch")
        return {
            "total_dispatches": len(dispatches),
            "executing": sum(1 for d in dispatches if d.get("status") == "执行中"),
            "completed": sum(1 for d in dispatches if d.get("status") == "已完成"),
            "failed": sum(1 for d in dispatches if d.get("status") == "派发失败"),
        }
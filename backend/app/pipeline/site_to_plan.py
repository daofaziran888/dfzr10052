"""站点登记→轮询计划 管线：站点验证后按历史变更率生成推荐的轮询频率与抓取深度计划。

核心行为：
- 站点已验证后读取其历史变更率
- 按变更率区间推荐轮询频率（高频>=30%、中频10-30%、低频<10%）
- 生成草稿计划单供审核生效
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.store import store


@dataclass
class PollPlanRecommendation:
    """轮询计划推荐结果。"""
    site_id: str
    site_name: str
    change_rate: float
    recommended_frequency: str
    recommended_depth: str
    plan_id: str = ""
    status: str = "未生成"

    def to_dict(self) -> dict[str, Any]:
        return {
            "site_id": self.site_id,
            "site_name": self.site_name,
            "change_rate": self.change_rate,
            "recommended_frequency": self.recommended_frequency,
            "recommended_depth": self.recommended_depth,
            "plan_id": self.plan_id,
            "status": self.status,
        }


class SiteToPlanEngine:
    """站点登记与轮询计划衔接引擎。"""

    def generate_plan_for_verified_site(self, site_entry: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
        """已验证站点按历史变更率生成推荐轮询计划。"""
        site_name = site_entry.get("站点名称", "")
        site_no = site_entry.get("站点编号", "")
        change_rate_str = site_entry.get("历史变更率", "0")
        try:
            change_rate = float(change_rate_str)
        except (ValueError, TypeError):
            change_rate = 0.0

        if change_rate >= 30.0:
            frequency = "高频轮询"
            depth = "全页抓取"
        elif change_rate >= 10.0:
            frequency = "中频轮询"
            depth = "关键字段"
        else:
            frequency = "低频轮询"
            depth = "索引页"

        rows = store.rows("poll_plan")
        plan_id = max((int(row.get("id", 0)) for row in rows), default=0) + 1
        plan_entry = {
            "id": plan_id,
            "计划编号": f"POLL-{plan_id:04d}",
            "站点编号": site_no,
            "轮询频率": frequency,
            "抓取深度": depth,
            "过滤规则": f"变更率_{change_rate:.1f}%",
            "创建时间": "2026-11-24",
            "status": "草稿",
            "pending": True,
            "abnormal": False,
        }
        rows.append(plan_entry)

        return True, (
            f"站点 {site_name} 变更率 {change_rate:.1f}%，推荐{frequency}/{depth}，"
            f"已生成计划 {plan_entry['计划编号']}"
        ), plan_entry

    def batch_from_verified_sites(self) -> tuple[int, list[dict[str, Any]]]:
        """从所有已验证站点批量生成计划。"""
        sites = store.rows("site_registry")
        verified = [s for s in sites if s.get("status") == "已验证"]
        results = []
        count = 0
        for site in verified:
            ok, msg, plan = self.generate_plan_for_verified_site(site)
            if ok and plan:
                results.append(plan)
                count += 1
        return count, results

    def get_plans_for_site(self, site_no: str) -> list[dict[str, Any]]:
        """获取某站点的全部轮询计划。"""
        rows = store.rows("poll_plan")
        return [r for r in rows if r.get("站点编号") == site_no]

    def snapshot(self) -> dict[str, Any]:
        rows = store.rows("poll_plan")
        plans = store.rows("poll_plan")
        return {
            "total_plans": len(plans),
            "by_frequency": {
                freq: sum(1 for p in plans if p.get("轮询频率") == freq)
                for freq in ["高频轮询", "中频轮询", "低频轮询"]
            },
        }
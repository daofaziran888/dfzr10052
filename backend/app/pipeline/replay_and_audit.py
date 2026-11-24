"""回放对比与审计 管线：快照重放检测稳定性验证与抽取流程审计。

核心行为：
- 用同一批次快照重放检测流程，与原事件对比差异
- 差异条数越限标记待判
- 按计划聚合操作审计与变更率统计
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.store import store


@dataclass
class ReplayCompareResult:
    compare_id: str
    plan_id: str
    orig_event_count: int
    replay_event_count: int
    diff_count: int
    compare_time: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "compare_id": self.compare_id,
            "plan_id": self.plan_id,
            "orig_event_count": self.orig_event_count,
            "replay_event_count": self.replay_event_count,
            "diff_count": self.diff_count,
            "compare_time": self.compare_time,
            "status": self.status,
        }


class ReplayCompareEngine:
    """回放对比引擎：用同一快照对重放检测流程对比原事件差异。"""

    REPLAY_DIFF_THRESHOLD = 2

    def replay_compare(
        self, plan_no: str, orig_count: int, replay_count: int,
    ) -> ReplayCompareResult:
        """重放检测流程对比原事件差异。"""
        rows = store.rows("replay_compare")
        compare_id = max((int(r.get("id", 0)) for r in rows), default=0) + 1

        diff_count = abs(orig_count - replay_count)
        status = "差异待判" if diff_count > self.REPLAY_DIFF_THRESHOLD else "已对比"

        result = ReplayCompareResult(
            compare_id=f"RCMP-{compare_id:04d}",
            plan_id=plan_no,
            orig_event_count=orig_count,
            replay_event_count=replay_count,
            diff_count=diff_count,
            compare_time="2026-11-24",
            status=status,
        )

        entry = {
            "id": compare_id,
            "对比编号": result.compare_id,
            "计划编号": plan_no,
            "原事件条数": str(orig_count),
            "重放事件条数": str(replay_count),
            "差异条数": str(diff_count),
            "对比时间": result.compare_time,
            "status": status,
            "pending": status == "差异待判",
            "abnormal": status == "差异待判",
        }
        rows.append(entry)
        return result

    def confirm_replay_result(self, compare_id: str) -> tuple[bool, str]:
        """确认回放对比结果。"""
        rows = store.rows("replay_compare")
        for r in rows:
            if r.get("对比编号") == compare_id:
                r["status"] = "已对比"
                r["pending"] = False
                return True, f"回放对比 {compare_id} 确认一致"
        return False, f"回放对比 {compare_id} 不存在"

    def snapshot(self) -> dict[str, Any]:
        rows = store.rows("replay_compare")
        return {
            "total_compares": len(rows),
            "confirmed": sum(1 for r in rows if r.get("status") == "已对比"),
            "pending_judge": sum(1 for r in rows if r.get("status") == "差异待判"),
        }


class AuditReportEngine:
    """审计与报告引擎：按计划聚合变更率与操作审计、输出对比报告。"""

    def generate_snapshot_report(self, site_no: str, period: str) -> dict[str, Any]:
        """为某站点生成周期对比报告。"""
        rows = store.rows("snapshot_report")
        report_id = max((int(r.get("id", 0)) for r in rows), default=0) + 1

        events = store.rows("change_event")
        change_count = len([e for e in events if e.get("发生时间", "").startswith(period[:7])])

        change_types = set()
        diffs = store.rows("diff_extract")
        for d in diffs:
            if d.get("抽取时间", "").startswith(period[:7]):
                change_types.add(d.get("差异类型", "未知"))

        entry = {
            "id": report_id,
            "报告编号": f"RPT-{report_id:04d}",
            "站点编号": site_no,
            "统计周期": period,
            "变化次数": str(change_count),
            "主要变化类型": "、".join(change_types) if change_types else "无",
            "生成时间": "2026-11-24",
            "status": "已发布",
            "pending": False,
            "abnormal": False,
        }
        rows.append(entry)
        return entry

    def build_timeline_entry(
        self, site_no: str, snap_seq: int, has_change: bool,
    ) -> dict[str, Any]:
        """生成一条历史时间线条目。"""
        rows = store.rows("history_timeline")
        tl_id = max((int(r.get("id", 0)) for r in rows), default=0) + 1

        entry = {
            "id": tl_id,
            "时间线编号": f"TL-{tl_id:04d}",
            "站点编号": site_no,
            "快照序号": str(snap_seq),
            "变化标记": "有变更" if has_change else "无变更",
            "时间点": "2026-11-24",
            "溯源状态": "待溯源" if has_change else "已溯源",
            "status": "待溯源" if has_change else "已溯源",
            "pending": has_change,
            "abnormal": False,
        }
        rows.append(entry)
        return entry

    def snapshot(self) -> dict[str, Any]:
        reports = store.rows("snapshot_report")
        timelines = store.rows("history_timeline")
        return {
            "total_reports": len(reports),
            "total_timelines": len(timelines),
        }
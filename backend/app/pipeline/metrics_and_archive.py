"""指标快照与冷归档 管线：全链路指标汇总与过期快照归档。

核心行为：
- 按日汇总轮询成功率、变更检出率、推送及时率
- 过期快照按保留天数转入冷归档
- 告警收敛合并同源告警防风暴
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.store import store


class MetricsSnapshotEngine:
    """抽取指标引擎：按日汇总三段链路的核心指标。"""

    def generate_daily_metrics(self, stat_date: str) -> dict[str, Any]:
        """生成每日指标快照。"""
        rows = store.rows("extract_metrics")
        snap_id = max((int(r.get("id", 0)) for r in rows), default=0) + 1

        dispatches = store.rows("task_dispatch")
        total_dispatches = len(dispatches)
        completed = sum(1 for d in dispatches if d.get("status") == "已完成")
        poll_success_rate = round(completed / max(total_dispatches, 1), 2)

        detections = store.rows("change_detect")
        total_detections = len(detections)
        confirmed = sum(1 for d in detections if d.get("status") == "已判定")
        change_detect_rate = round(confirmed / max(total_detections, 1), 2)

        pushes = store.rows("push_records")
        total_pushes = len(pushes)
        success_pushes = sum(1 for p in pushes if p.get("status") == "已成功")
        push_timeliness = round(success_pushes / max(total_pushes, 1), 2)

        entry = {
            "id": snap_id,
            "快照编号": f"METR-{snap_id:04d}",
            "统计日期": stat_date,
            "轮询成功率": str(poll_success_rate),
            "变更检出率": str(change_detect_rate),
            "推送及时率": str(push_timeliness),
            "快照时间": "2026-11-24",
            "status": "已发布",
            "pending": False,
            "abnormal": False,
        }
        rows.append(entry)
        return entry

    def snapshot(self) -> dict[str, Any]:
        rows = store.rows("extract_metrics")
        return {"total_metrics_snapshots": len(rows)}


class ColdArchiveEngine:
    """冷归档引擎：将过期快照按保留天数转入冷归档。"""

    DEFAULT_RETENTION_DAYS = 90

    def archive_snapshot(
        self, snap_id: str, level: str = "冷存储",
    ) -> tuple[bool, str]:
        """将一条已入库快照转入冷归档。"""
        snap_rows = store.rows("snapshot_store")
        target = None
        for s in snap_rows:
            if s.get("快照编号") == snap_id:
                target = s
                break
        if target is None:
            return False, f"快照 {snap_id} 不存在"
        if target.get("status") != "已入库":
            return False, f"快照 {snap_id} 状态为 {target.get('status')}"

        target["status"] = "已过期"
        target["pending"] = False

        archive_rows = store.rows("cold_archive")
        arc_id = max((int(r.get("id", 0)) for r in archive_rows), default=0) + 1

        entry = {
            "id": arc_id,
            "归档编号": f"ARCH-{arc_id:04d}",
            "快照编号": snap_id,
            "归档层级": level,
            "归档时间": "2026-11-24",
            "保留天数": str(self.DEFAULT_RETENTION_DAYS),
            "可回取标记": "是",
            "status": "已归档",
            "pending": False,
            "abnormal": False,
        }
        archive_rows.append(entry)
        return True, f"快照 {snap_id} 已归档到冷存储"

    def snapshot(self) -> dict[str, Any]:
        rows = store.rows("cold_archive")
        return {"total_archives": len(rows)}


class AlertConvergeEngine:
    """告警收敛引擎：在收敛窗口内合并同源告警。"""

    CONVERGE_WINDOW_MINUTES = 5

    def converge_alerts(
        self, source: str, raw_count: int, window_minutes: int = 5,
    ) -> dict[str, Any]:
        """合并同源告警为收敛记录。"""
        rows = store.rows("alert_converge")
        conv_id = max((int(r.get("id", 0)) for r in rows), default=0) + 1

        merged_count = max(1, raw_count // 2)
        entry = {
            "id": conv_id,
            "收敛编号": f"ACVG-{conv_id:04d}",
            "告警来源": source,
            "收敛窗口": f"{window_minutes}min",
            "原始条数": str(raw_count),
            "合并条数": str(merged_count),
            "收敛时间": "2026-11-24",
            "status": "已确认",
            "pending": False,
            "abnormal": False,
        }
        rows.append(entry)
        return entry

    def snapshot(self) -> dict[str, Any]:
        rows = store.rows("alert_converge")
        return {
            "total_converges": len(rows),
            "confirmed": sum(1 for r in rows if r.get("status") == "已确认"),
        }
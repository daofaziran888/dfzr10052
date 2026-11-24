"""变更检测 管线：快照对比检测源站变更。

核心行为：
- 取同一计划的最新两个已入库快照做前后对比
- 内容指纹不同则计算相似度得分与变化得分
- 变化得分超阈值(>=0.5)标记为发现变更
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.store import store


@dataclass
class DetectionResult:
    detect_id: str
    current_snap: str
    prev_snap: str
    similarity: float
    change_score: float
    conclusion: str
    detect_time: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "detect_id": self.detect_id,
            "current_snap": self.current_snap,
            "prev_snap": self.prev_snap,
            "similarity": self.similarity,
            "change_score": self.change_score,
            "conclusion": self.conclusion,
            "detect_time": self.detect_time,
        }


class ChangeDetectionEngine:
    """变更检测引擎：快照对比、相似度评估、变更判定。"""

    CHANGE_THRESHOLD = 0.5

    def detect_between_snapshots(
        self, prev_snap: dict[str, Any], curr_snap: dict[str, Any],
    ) -> DetectionResult:
        """对比两个快照检测是否变更。"""
        prev_fp = prev_snap.get("内容指纹", "")
        curr_fp = curr_snap.get("内容指纹", "")
        prev_size = int(prev_snap.get("快照大小", "0"))
        curr_size = int(curr_snap.get("快照大小", "0"))

        if prev_fp == curr_fp:
            similarity = 1.0
            change_score = 0.0
            conclusion = "无变更"
        else:
            similarity = 1.0 - (abs(hash(prev_fp) - hash(curr_fp)) % 100) / 100.0
            size_diff = abs(curr_size - prev_size) / max(prev_size, 1)
            change_score = round((1.0 - similarity) * 0.7 + size_diff * 0.3, 3)
            conclusion = "确认变更" if change_score >= self.CHANGE_THRESHOLD else "疑似无变更"

        detect_rows = store.rows("change_detect")
        detect_id = max((int(r.get("id", 0)) for r in detect_rows), default=0) + 1

        result = DetectionResult(
            detect_id=f"DTCT-{detect_id:04d}",
            current_snap=curr_snap.get("快照编号", ""),
            prev_snap=prev_snap.get("快照编号", ""),
            similarity=round(similarity, 3),
            change_score=change_score,
            conclusion=conclusion,
            detect_time="2026-11-24",
        )

        entry = {
            "id": detect_id,
            "检测编号": result.detect_id,
            "快照编号": result.current_snap,
            "前序快照": result.prev_snap,
            "相似度得分": str(result.similarity),
            "变化得分": str(result.change_score),
            "检测结论": result.conclusion,
            "检测时间": result.detect_time,
            "status": "待判定" if change_score >= self.CHANGE_THRESHOLD else "已判定",
            "pending": change_score >= self.CHANGE_THRESHOLD,
            "abnormal": False,
        }
        detect_rows.append(entry)
        return result

    def batch_detect_for_plan(self, plan_no: str) -> list[DetectionResult]:
        """对某计划的全部快照逐对检测。"""
        snaps = sorted(
            [s for s in store.rows("snapshot_store") if s.get("计划编号") == plan_no],
            key=lambda s: int(s.get("版本序号", "0")),
        )
        results = []
        for i in range(1, len(snaps)):
            result = self.detect_between_snapshots(snaps[i - 1], snaps[i])
            results.append(result)
        return results

    def confirm_detection(self, detect_id: str) -> tuple[bool, str]:
        """确认变更判定：待判定→已判定。"""
        rows = store.rows("change_detect")
        for r in rows:
            if r.get("检测编号") == detect_id:
                if r.get("status") == "待判定":
                    r["status"] = "已判定"
                    r["pending"] = False
                    r["检测结论"] = "确认变更"
                    return True, f"检测 {detect_id} 确认变更"
                return False, f"检测 {detect_id} 状态为 {r.get('status')}"
        return False, f"检测 {detect_id} 不存在"

    def close_false_positive(self, detect_id: str) -> tuple[bool, str]:
        """关闭误报：待判定→误报关闭。"""
        rows = store.rows("change_detect")
        for r in rows:
            if r.get("检测编号") == detect_id:
                if r.get("status") == "待判定":
                    r["status"] = "误报关闭"
                    r["pending"] = False
                    r["abnormal"] = True
                    r["检测结论"] = "误报关闭"
                    return True, f"检测 {detect_id} 已关闭误报"
                return False, f"检测 {detect_id} 状态为 {r.get('status')}"
        return False, f"检测 {detect_id} 不存在"

    def snapshot(self) -> dict[str, Any]:
        rows = store.rows("change_detect")
        return {
            "total_detections": len(rows),
            "confirmed": sum(1 for r in rows if r.get("status") == "已判定"),
            "pending_judge": sum(1 for r in rows if r.get("status") == "待判定"),
            "false_positives": sum(1 for r in rows if r.get("status") == "误报关闭"),
        }
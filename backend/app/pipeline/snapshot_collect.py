"""快照采集 管线：任务执行→抓取页面内容→生成站点快照→内容指纹计算。

核心行为：
- 执行中的派发任务完成抓取后生成快照条目
- 快照通过内容指纹标识源站状态
- 快照版本序号递增、关联计划编号
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import hashlib

from app.store import store


@dataclass
class CollectedSnapshot:
    snapshot_id: str
    plan_id: str
    site_no: str
    content_hash: str
    size_kb: int
    partition: str
    version_seq: int
    collect_time: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "plan_id": self.plan_id,
            "site_no": self.site_no,
            "content_hash": self.content_hash,
            "size_kb": self.size_kb,
            "partition": self.partition,
            "version_seq": self.version_seq,
            "collect_time": self.collect_time,
            "status": self.status,
        }


class SnapshotCollectEngine:
    """快照采集引擎：模拟抓取、生成内容指纹、记录版本。"""

    def collect_from_dispatch(self, dispatch_entry: dict[str, Any]) -> CollectedSnapshot:
        """任务派发执行完成后生成一条站点快照。"""
        plan_no = dispatch_entry.get("计划编号", "")
        plans = [p for p in store.rows("poll_plan") if p.get("计划编号") == plan_no]
        site_no = plans[0].get("站点编号", "") if plans else "UNKNOWN"

        existing_snaps = [
            s for s in store.rows("snapshot_store")
            if s.get("计划编号") == plan_no
        ]
        version_seq = len(existing_snaps) + 1

        raw_content = f"{site_no}|v{version_seq}|{dispatch_entry.get('派发时间','')}"
        content_hash = hashlib.sha256(raw_content.encode()).hexdigest()[:16]
        size_kb = (len(raw_content) % 50) + 10
        partition = f"snap-{site_no[:4]}"

        snap_rows = store.rows("snapshot_store")
        snap_id = max((int(r.get("id", 0)) for r in snap_rows), default=0) + 1

        snap = CollectedSnapshot(
            snapshot_id=f"SNAP-{snap_id:04d}",
            plan_id=plan_no,
            site_no=site_no,
            content_hash=content_hash,
            size_kb=size_kb,
            partition=partition,
            version_seq=version_seq,
            collect_time="2026-11-24",
            status="待校验",
        )

        entry = {
            "id": snap_id,
            "快照编号": snap.snapshot_id,
            "计划编号": plan_no,
            "抓取时间": snap.collect_time,
            "内容指纹": content_hash,
            "快照大小": str(size_kb),
            "存储分区": partition,
            "版本序号": str(version_seq),
            "status": "待校验",
            "pending": True,
            "abnormal": False,
        }
        snap_rows.append(entry)
        return snap

    def confirm_snapshot(self, snap_id: str) -> tuple[bool, str]:
        """确认快照入库：待校验→已入库。"""
        rows = store.rows("snapshot_store")
        for r in rows:
            if r.get("快照编号") == snap_id:
                if r.get("status") == "待校验":
                    r["status"] = "已入库"
                    r["pending"] = False
                    return True, f"快照 {snap_id} 已入库"
                return False, f"快照 {snap_id} 状态为 {r.get('status')}"
        return False, f"快照 {snap_id} 不存在"

    def get_latest_snap_for_site(self, site_no: str) -> dict[str, Any] | None:
        """获取某站点最新快照。"""
        rows = store.rows("snapshot_store")
        site_snaps = [r for r in rows if r.get("计划编号", "").startswith("POLL-")]
        if not site_snaps:
            return None
        return max(site_snaps, key=lambda r: int(r.get("版本序号", "0")))

    def snapshot(self) -> dict[str, Any]:
        rows = store.rows("snapshot_store")
        return {
            "total_snapshots": len(rows),
            "pending_verify": sum(1 for r in rows if r.get("status") == "待校验"),
            "confirmed": sum(1 for r in rows if r.get("status") == "已入库"),
        }
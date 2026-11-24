"""全链路编排器：串联各管线组件形成端到端流程。

编排流程：
1. 站点登记→轮询计划生成
2. 预算校验→任务派发
3. 快照采集→内容指纹计算
4. 快照对比→变更检测
5. 噪声过滤→字段映射
6. 差异解析→事件发布→去重→订阅推送
7. 质量抽样→批次封窗
8. 回放对比→检测稳定性验证
9. 指标快照→全链路指标汇总
10. 冷归档→过期快照归档
"""
from __future__ import annotations

from typing import Any

from app.pipeline.site_to_plan import SiteToPlanEngine
from app.pipeline.dispatch_and_budget import DispatchBudgetEngine
from app.pipeline.snapshot_collect import SnapshotCollectEngine
from app.pipeline.change_detection import ChangeDetectionEngine
from app.pipeline.noise_and_mapping import NoiseFilterEngine, FieldMappingEngine
from app.pipeline.diff_and_event import DiffExtractEngine, EventPublishEngine
from app.pipeline.batch_and_quality import ExtractBatchEngine, QualitySampleEngine
from app.pipeline.replay_and_audit import ReplayCompareEngine, AuditReportEngine
from app.pipeline.metrics_and_archive import MetricsSnapshotEngine, ColdArchiveEngine, AlertConvergeEngine

from app.store import store


class PipelineOrchestrator:
    """全链路编排器。"""

    def __init__(self):
        self.site_plan = SiteToPlanEngine()
        self.dispatch = DispatchBudgetEngine()
        self.snap_collect = SnapshotCollectEngine()
        self.change_detect = ChangeDetectionEngine()
        self.noise_filter = NoiseFilterEngine()
        self.field_map = FieldMappingEngine()
        self.diff_extract = DiffExtractEngine()
        self.event_pub = EventPublishEngine()
        self.batch_engine = ExtractBatchEngine()
        self.quality = QualitySampleEngine()
        self.replay = ReplayCompareEngine()
        self.audit = AuditReportEngine()
        self.metrics = MetricsSnapshotEngine()
        self.archive = ColdArchiveEngine()
        self.alert = AlertConvergeEngine()

    def run_full_pipeline(self, site_no: str, plan_no: str) -> dict[str, Any]:
        """执行全链路端到端流程。"""
        result: dict[str, Any] = {"steps": []}

        # Step1: 生成计划
        sites = [s for s in store.rows("site_registry") if s.get("站点编号") == site_no]
        if sites:
            ok, msg, plan = self.site_plan.generate_plan_for_verified_site(sites[0])
            result["steps"].append({"name": "站点登记→轮询计划", "ok": ok, "msg": msg})

        # Step2: 派发
        dispatch_results = self.dispatch.dispatch_active_plans()
        result["steps"].append({"name": "预算校验→任务派发", "dispatches": len(dispatch_results)})

        # Step3: 快照采集
        dispatches = store.rows("task_dispatch")
        for d in dispatches[:2]:
            snap = self.snap_collect.collect_from_dispatch(d)
            result["steps"].append({"name": "快照采集", "snap_id": snap.snapshot_id})

        # Step4: 变更检测
        snaps = store.rows("snapshot_store")
        if len(snaps) >= 2:
            detection = self.change_detect.detect_between_snapshots(snaps[-2], snaps[-1])
            result["steps"].append({"name": "变更检测", "detect_id": detection.detect_id, "conclusion": detection.conclusion})

            # Step5: 噪声过滤
            noise = self.noise_filter.filter_detection_changes(detection.detect_id, 3)
            result["steps"].append({"name": "噪声过滤", "retained": noise.retained_count})

            # Step6: 差异解析
            diffs = self.diff_extract.extract_diff_blocks(
                detection.detect_id,
                [{"source": "title", "target": "站点标题"}],
            )
            result["steps"].append({"name": "差异解析", "diff_id": diffs.diff_id})

            # Step7: 确认差异 + 创建事件 + 去重 + 推送
            self.diff_extract.confirm_diff_block(diffs.diff_id)
            event = self.event_pub.create_event_from_diff(diffs)
            self.event_pub.deduplicate_event(event.event_id)
            self.event_pub.push_event_to_subscriber(event.event_id)
            result["steps"].append({"name": "事件发布推送给订阅方", "event_id": event.event_id})

        # Step8: 批次封窗 + 质量抽样
        batch = self.batch_engine.create_batch(plan_no, "2026-11-24 00:00", "2026-11-24 23:59")
        self.batch_engine.seal_batch(batch.batch_id)
        sample = self.quality.sample_batch(batch.batch_id)
        result["steps"].append({"name": "批次封窗+质量抽样", "batch_id": batch.batch_id, "pass_rate": sample.pass_rate})

        # Step9: 回放对比
        replay = self.replay.replay_compare(plan_no, 5, 6)
        result["steps"].append({"name": "回放对比", "diff_count": replay.diff_count})

        # Step10: 指标快照+归档+告警收敛
        metrics_entry = self.metrics.generate_daily_metrics("2026-11-24")
        result["steps"].append({"name": "指标快照生成", "snap_id": metrics_entry.get("快照编号")})

        if snaps:
            self.archive.archive_snapshot(snaps[0].get("快照编号", ""))
            result["steps"].append({"name": "冷归档"})

        self.alert.converge_alerts(site_no, 3)
        result["steps"].append({"name": "告警收敛"})

        return result

    def full_snapshot(self) -> dict[str, Any]:
        """汇总全部管线引擎的运行快照。"""
        return {
            "site_plan": self.site_plan.snapshot(),
            "dispatch": self.dispatch.snapshot(),
            "snapshot_collect": self.snap_collect.snapshot(),
            "change_detect": self.change_detect.snapshot(),
            "noise_filter": self.noise_filter.snapshot(),
            "field_map": self.field_map.snapshot(),
            "event_pub": self.event_pub.snapshot(),
            "batch": self.batch_engine.snapshot(),
            "quality": self.quality.snapshot(),
            "replay": self.replay.snapshot(),
            "audit": self.audit.snapshot(),
            "metrics": self.metrics.snapshot(),
            "archive": self.archive.snapshot(),
            "alert": self.alert.snapshot(),
        }
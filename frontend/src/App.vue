<template>
  <div class="app-shell">
    <aside class="app-side">
      <h1 class="app-title">巡更工坊 · 源站变更轮询与差异抽取平台</h1>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <header class="app-head">
        <span class="head-desc">面向轮询计划、站点快照、变更检测、差异抽取、变更事件订阅推送与噪声过滤的源站变更采集平台。</span>
        <span class="head-user">当前值班：数据工程组</span>
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
const navItems = [{ label: "运营概览", path: "/" }, { label: "轮询计划", path: "/poll_plan" }, { label: "快照存储", path: "/snapshot_store" }, { label: "变更检测", path: "/change_detect" }, { label: "差异抽取", path: "/diff_extract" }, { label: "变更事件", path: "/change_event" }, { label: "字段映射", path: "/field_mapping" }, { label: "抽取批次", path: "/extract_batch" }, { label: "抓取预算", path: "/crawl_budget" }, { label: "站点登记", path: "/site_registry" }, { label: "工作节点", path: "/poll_worker" }, { label: "任务派发", path: "/task_dispatch" }, { label: "噪声过滤", path: "/noise_filter" }, { label: "事件去重", path: "/event_dedup" }, { label: "订阅路由", path: "/subscribe_route" }, { label: "推送台账", path: "/push_records" }, { label: "对比报告", path: "/snapshot_report" }, { label: "历史时间线", path: "/history_timeline" }, { label: "质量抽样", path: "/quality_sample" }, { label: "回放对比", path: "/replay_compare" }, { label: "抽取指标", path: "/extract_metrics" }, { label: "冷归档", path: "/cold_archive" }, { label: "告警收敛", path: "/alert_converge" }]
</script>

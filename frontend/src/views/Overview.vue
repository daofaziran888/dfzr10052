<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。</p>
      </div>
    </header>
    <div class="stat-row">
      <article v-for="card in cards" :key="card.label" class="stat-card">
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
    </div>
    <table class="data-table">
      <thead>
        <tr><th>业务模块</th><th>今日新增</th><th>待处理</th><th>异常量</th></tr>
      </thead>
      <tbody>
        <tr v-for="row in moduleRows" :key="row.name">
          <td>{{ row.name }}</td>
          <td>{{ row.created }}</td>
          <td>{{ row.pending }}</td>
          <td>{{ row.abnormal }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'

type Overview = {
  cards: { label: string; value: number }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
}

const cards = ref<Overview['cards']>([])
const moduleRows = ref<Overview['modules']>([])

onMounted(async () => {
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    cards.value = payload.cards
    moduleRows.value = payload.modules
  } catch {
    cards.value = [{"label": "业务模块", "value": 0}, {"label": "今日新增", "value": 0}]
    moduleRows.value = [{"name": "轮询计划", "created": 0, "pending": 0, "abnormal": 0}, {"name": "快照存储", "created": 0, "pending": 0, "abnormal": 0}, {"name": "变更检测", "created": 0, "pending": 0, "abnormal": 0}, {"name": "差异抽取", "created": 0, "pending": 0, "abnormal": 0}, {"name": "变更事件", "created": 0, "pending": 0, "abnormal": 0}, {"name": "字段映射", "created": 0, "pending": 0, "abnormal": 0}, {"name": "抽取批次", "created": 0, "pending": 0, "abnormal": 0}, {"name": "抓取预算", "created": 0, "pending": 0, "abnormal": 0}, {"name": "站点登记", "created": 0, "pending": 0, "abnormal": 0}, {"name": "工作节点", "created": 0, "pending": 0, "abnormal": 0}, {"name": "任务派发", "created": 0, "pending": 0, "abnormal": 0}, {"name": "噪声过滤", "created": 0, "pending": 0, "abnormal": 0}, {"name": "事件去重", "created": 0, "pending": 0, "abnormal": 0}, {"name": "订阅路由", "created": 0, "pending": 0, "abnormal": 0}, {"name": "推送台账", "created": 0, "pending": 0, "abnormal": 0}, {"name": "对比报告", "created": 0, "pending": 0, "abnormal": 0}, {"name": "历史时间线", "created": 0, "pending": 0, "abnormal": 0}, {"name": "质量抽样", "created": 0, "pending": 0, "abnormal": 0}, {"name": "回放对比", "created": 0, "pending": 0, "abnormal": 0}, {"name": "抽取指标", "created": 0, "pending": 0, "abnormal": 0}, {"name": "冷归档", "created": 0, "pending": 0, "abnormal": 0}, {"name": "告警收敛", "created": 0, "pending": 0, "abnormal": 0}]
  }
})
</script>

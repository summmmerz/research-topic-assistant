<template>
  <section class="view">
    <header class="view-head">
      <div>
        <h1>知识图谱</h1>
        <p>浏览论文、作者、机构、关键词与研究方向之间的关联结构。</p>
      </div>
      <div class="search-row">
        <el-input
          v-model="query"
          placeholder="关键词、论文、导师或方向"
          @keyup.enter="loadGraph"
        />
        <el-button type="primary" @click="loadGraph">
          <el-icon><Search /></el-icon>
        </el-button>
      </div>
    </header>
    <section class="kg-metrics">
      <div><span>存储</span><strong>{{ storageLabel }}</strong></div>
      <div><span>实体</span><strong>{{ status.total_nodes || 0 }}</strong></div>
      <div><span>关系</span><strong>{{ status.total_edges || 0 }}</strong></div>
      <div><span>密度</span><strong>{{ status.density || 0 }}</strong></div>
    </section>
    <p v-if="status.fallback_reason" class="status-note">
      Neo4j 未连接，论文部署形态未就绪：{{ status.fallback_reason }}
    </p>
    <KnowledgeGraph :graph="graph" @node-click="loadFocus" />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import KnowledgeGraph from '../components/KnowledgeGraph.vue'
import { getEntityGraph, getKnowledgeGraph, getKnowledgeGraphStatus } from '../api/client'

const query = ref('知识图谱')
const graph = ref<any>({ nodes: [], edges: [], legend: [] })
const status = ref<any>({})
const storageLabel = computed(() => {
  if (status.value.storage === 'neo4j') return 'Neo4j'
  if (status.value.storage === 'json_fallback') return '需连接 Neo4j'
  return status.value.storage || '检查中'
})

async function loadGraph() {
  graph.value = await getKnowledgeGraph({ query: query.value, max_nodes: 45 })
  const payload = await getKnowledgeGraphStatus()
  status.value = payload.status || {}
}

async function loadFocus(id: string) {
  graph.value = await getEntityGraph(id)
}

onMounted(loadGraph)
</script>

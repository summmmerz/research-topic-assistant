<template>
  <el-container class="shell">
    <el-aside class="rail" width="232px">
      <div class="brand">
        <span class="brand-mark">RA</span>
        <div>
          <strong>研学助手</strong>
          <small>KG + LLM</small>
        </div>
      </div>
      <el-menu router :default-active="$route.path" class="nav">
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>智能问答</span>
        </el-menu-item>
        <el-menu-item index="/knowledge-graph">
          <el-icon><Share /></el-icon>
          <span>知识图谱</span>
        </el-menu-item>
        <el-menu-item index="/topic-recommendation">
          <el-icon><Aim /></el-icon>
          <span>选题推荐</span>
        </el-menu-item>
      </el-menu>
      <div class="health">
        <span :class="['dot', health?.status === 'healthy' ? 'ok' : 'warn']"></span>
        <span>{{ healthLabel }}</span>
      </div>
    </el-aside>
    <el-main class="workspace">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Aim, ChatDotRound, Share } from '@element-plus/icons-vue'
import { getHealth } from './api/client'

const health = ref<any>(null)
const healthLabel = computed(() => {
  if (!health.value) return '检查中'
  return health.value.deployment_ready ? '部署就绪' : '部署未就绪'
})

onMounted(async () => {
  try {
    health.value = await getHealth()
  } catch {
    health.value = { status: 'degraded', deployment_ready: false }
  }
})
</script>

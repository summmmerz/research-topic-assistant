<template>
  <section class="view">
    <header class="view-head">
      <div>
        <h1>分阶段选题推荐</h1>
        <p>融合语义、趋势、图谱中心性与导师匹配特征。</p>
      </div>
      <el-button @click="start" type="primary">新会话</el-button>
    </header>
    <section v-if="stageData" class="stage-panel">
      <el-steps :active="stageData.stage - 1" finish-status="success">
        <el-step v-for="n in 5" :key="n" :title="`阶段 ${n}`" />
      </el-steps>
      <h2>{{ stageData.title }}</h2>
      <p>{{ stageData.description }}</p>
      <div v-if="stageData.type === 'multiple_choice'" class="option-grid">
        <el-button v-for="option in stageData.options" :key="option" @click="submit({ selection: option })">
          {{ option }}
        </el-button>
      </div>
      <form v-else-if="stageData.type === 'text_input'" class="stage-form" @submit.prevent="submit({ input })">
        <el-input v-model="input" type="textarea" :rows="5" :placeholder="stageData.placeholder" />
        <el-button type="primary" native-type="submit">提交</el-button>
      </form>
    </section>
    <section class="rec-grid" v-if="recommendations.length">
      <RecommendationCard
        v-for="item in recommendations"
        :key="item.id || item.topic_key"
        :item="item"
        @feedback="handleFeedback"
      />
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import RecommendationCard from '../components/RecommendationCard.vue'
import { createStageSession, getStageData, submitFeedback, submitStage } from '../api/client'

const sessionId = ref('')
const stageData = ref<any>(null)
const recommendations = ref<any[]>([])
const input = ref('')

async function start() {
  const data = await createStageSession()
  sessionId.value = data.session_id
  stageData.value = data.stage_data
  recommendations.value = []
}

async function submit(payload: Record<string, unknown>) {
  const data = await submitStage(sessionId.value, stageData.value.stage, payload)
  if (data.recommendations) {
    recommendations.value = data.recommendations
    stageData.value = {
      stage: 6,
      title: '推荐完成',
      description: '已生成候选选题。',
      type: 'completed'
    }
  } else {
    const next = await getStageData(sessionId.value, data.next_stage)
    stageData.value = next.stage_data
  }
  input.value = ''
}

async function handleFeedback(item: any, feedbackType: string) {
  await submitFeedback({
    session_id: sessionId.value,
    recommendation_id: item.id || item.topic_id || item.topic_key,
    topic_key: item.topic_key,
    feedback_type: feedbackType
  })
  ElMessage.success('反馈已记录')
}

onMounted(start)
</script>

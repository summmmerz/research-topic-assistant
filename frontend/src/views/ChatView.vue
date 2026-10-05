<template>
  <section class="view">
    <header class="view-head">
      <div>
        <h1>智能问答</h1>
        <p>面向科研选题、概念解释和知识图谱事实查询。</p>
      </div>
    </header>
    <main class="chat-grid">
      <div class="messages">
        <ChatMessage
          v-for="message in messages"
          :key="message.id"
          :role="message.role"
          :content="message.content"
          :timestamp="message.timestamp"
        />
      </div>
      <form class="composer" @submit.prevent="submit">
        <el-input
          v-model="draft"
          type="textarea"
          :rows="4"
          resize="none"
          placeholder="输入科研问题，例如：知识图谱和推荐系统有什么关联？"
        />
        <el-button type="primary" native-type="submit" :loading="loading">
          <el-icon><Promotion /></el-icon>
        </el-button>
      </form>
    </main>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Promotion } from '@element-plus/icons-vue'
import ChatMessage from '../components/ChatMessage.vue'
import { sendChat } from '../api/client'

const draft = ref('知识图谱和推荐系统有什么关联？')
const loading = ref(false)
const sessionId = `vue-${Date.now()}`
const messages = ref<any[]>([])

async function submit() {
  if (!draft.value.trim()) return
  const content = draft.value
  messages.value.push({
    id: crypto.randomUUID(),
    role: 'user',
    content,
    timestamp: new Date().toLocaleTimeString()
  })
  draft.value = ''
  loading.value = true
  try {
    const data = await sendChat(content, sessionId)
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'assistant',
      content: data.response || data.error || '暂无回复',
      timestamp: new Date().toLocaleTimeString()
    })
  } finally {
    loading.value = false
  }
}
</script>

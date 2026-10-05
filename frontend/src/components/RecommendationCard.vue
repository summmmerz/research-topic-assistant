<template>
  <section class="rec-card">
    <header>
      <strong>{{ item.title || item.topic_name }}</strong>
      <el-tag size="small" type="success">{{ item.total_score }}</el-tag>
    </header>
    <p>{{ item.background || item.description }}</p>
    <div class="tags">
      <el-tag v-for="tag in item.reason_tags || []" :key="tag" size="small">{{ tag }}</el-tag>
    </div>
    <p class="explain">{{ item.explanation_summary || item.explanation }}</p>
    <dl class="scores" v-if="item.features">
      <div v-for="(value, key) in item.features" :key="key">
        <dt>{{ key }}</dt>
        <dd>{{ value }}</dd>
      </div>
    </dl>
    <footer class="feedback-row">
      <el-button size="small" @click="$emit('feedback', item, 'like')">有帮助</el-button>
      <el-button size="small" @click="$emit('feedback', item, 'bookmark')">收藏</el-button>
      <el-button size="small" text @click="$emit('feedback', item, 'ignore')">暂不采用</el-button>
    </footer>
  </section>
</template>

<script setup lang="ts">
defineProps<{ item: any }>()
defineEmits<{ feedback: [item: any, feedbackType: string] }>()
</script>

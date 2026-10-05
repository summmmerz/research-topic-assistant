<template>
  <article :class="['message', role]">
    <div class="avatar">{{ role === 'user' ? 'U' : 'A' }}</div>
    <div class="bubble">
      <p>{{ content }}</p>
      <time>{{ timestamp }}</time>
    </div>
  </article>
</template>

<script setup lang="ts">
defineProps<{
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}>()
</script>

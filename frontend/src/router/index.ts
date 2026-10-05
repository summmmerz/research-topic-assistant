import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import KnowledgeGraphView from '../views/KnowledgeGraphView.vue'
import TopicRecommendationView from '../views/TopicRecommendationView.vue'

export default createRouter({
  history: createWebHistory('/vue/'),
  routes: [
    { path: '/', redirect: '/chat' },
    { path: '/chat', component: ChatView },
    { path: '/knowledge-graph', component: KnowledgeGraphView },
    { path: '/topic-recommendation', component: TopicRecommendationView }
  ]
})

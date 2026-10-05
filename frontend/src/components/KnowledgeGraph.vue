<template>
  <div ref="chartEl" class="graph-canvas"></div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{ graph: any }>()
const emit = defineEmits<{ nodeClick: [id: string] }>()
const chartEl = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

function render() {
  if (!chartEl.value) return
  chart = chart || echarts.init(chartEl.value)
  const nodes = (props.graph?.nodes || []).map((node: any) => ({
    id: node.id,
    name: node.label,
    value: node.degree || 1,
    category: node.type,
    symbolSize: Math.max(18, Math.min(58, 18 + (node.degree || 1) * 7))
  }))
  const categories = (props.graph?.legend || []).map((item: any) => ({ name: item.type }))
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { top: 8, left: 8, data: categories.map((item: any) => item.name) },
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        categories,
        data: nodes,
        links: (props.graph?.edges || []).map((edge: any) => ({
          source: edge.source,
          target: edge.target,
          label: { show: false, formatter: edge.relation }
        })),
        force: { repulsion: 180, edgeLength: 90 },
        label: { show: true, position: 'right', fontSize: 11 },
        lineStyle: { color: '#7a8794', opacity: 0.72 }
      }
    ]
  })
  chart.off('click')
  chart.on('click', (params: any) => {
    if (params.dataType === 'node' && params.data?.id) {
      emit('nodeClick', params.data.id)
    }
  })
}

watch(() => props.graph, render, { deep: true })
onMounted(() => {
  render()
  window.addEventListener('resize', () => chart?.resize())
})
onBeforeUnmount(() => chart?.dispose())
</script>

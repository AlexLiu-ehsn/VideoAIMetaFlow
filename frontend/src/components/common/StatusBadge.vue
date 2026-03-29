<script setup lang="ts">
import type { VideoStatus } from '@/types'

interface Props {
  status: VideoStatus
}

defineProps<Props>()

const statusConfig: Record<VideoStatus, { label: string; color: string; pulse: boolean }> = {
  pending: { label: '等待中', color: 'var(--color-text-muted)', pulse: false },
  uploading_to_gemini: { label: '上傳分析中', color: 'var(--color-warning)', pulse: true },
  analyzing: { label: '分析中', color: 'var(--color-primary-400)', pulse: true },
  completed: { label: '已完成', color: 'var(--color-success)', pulse: false },
  failed: { label: '失敗', color: 'var(--color-error)', pulse: false },
}
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium uppercase tracking-[0.08em]"
    :style="{ color: statusConfig[status].color }"
    style="font-family: var(--font-label)"
  >
    <span
      class="w-2 h-2 rounded-full"
      :class="{ 'animate-pulse': statusConfig[status].pulse }"
      :style="{
        backgroundColor: statusConfig[status].color,
        boxShadow: `0 0 6px ${statusConfig[status].color}`,
      }"
    />
    {{ statusConfig[status].label }}
  </span>
</template>

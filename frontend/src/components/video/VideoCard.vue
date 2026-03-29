<script setup lang="ts">
import type { VideoSummary } from '@/types'
import { getThumbnailUrl } from '@/api/videos'
import BaseBadge from '@/components/common/BaseBadge.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

interface Props {
  video: VideoSummary
}

defineProps<Props>()

function formatDuration(seconds: number | null): string {
  if (!seconds) return '--:--'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}
</script>

<template>
  <RouterLink
    :to="`/videos/${video.id}`"
    class="group block bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-[rgba(0,255,136,0.3)] hover:shadow-[var(--shadow-sm)] transition-all duration-300 overflow-hidden"
    style="clip-path: var(--chamfer)"
  >
    <!-- 縮圖 -->
    <div class="relative aspect-video bg-[var(--color-surface-hover)] overflow-hidden">
      <img
        v-if="video.thumbnail"
        :src="getThumbnailUrl(video.id)"
        :alt="video.filename"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-[var(--color-text-muted)]">
        <svg class="w-12 h-12 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
        </svg>
      </div>

      <!-- HUD 角落裝飾 -->
      <div class="absolute top-1.5 left-1.5 w-3 h-3 border-t border-l border-[var(--color-primary-400)] opacity-50" />
      <div class="absolute top-1.5 right-1.5 w-3 h-3 border-t border-r border-[var(--color-primary-400)] opacity-50" />
      <div class="absolute bottom-1.5 left-1.5 w-3 h-3 border-b border-l border-[var(--color-primary-400)] opacity-50" />
      <div class="absolute bottom-1.5 right-1.5 w-3 h-3 border-b border-r border-[var(--color-primary-400)] opacity-50" />

      <!-- 時長標籤 -->
      <span
        v-if="video.duration"
        class="absolute bottom-2 right-2 px-2 py-0.5 bg-[rgba(10,10,15,0.85)] text-[var(--color-primary-400)] text-xs"
        style="clip-path: var(--chamfer-sm); font-family: var(--font-label)"
      >
        {{ formatDuration(video.duration) }}
      </span>
    </div>

    <!-- 資訊 -->
    <div class="p-3">
      <h3 class="text-sm font-medium text-[var(--color-text-primary)] truncate mb-1">
        {{ video.filename }}
      </h3>

      <div
        class="flex items-center gap-2 text-xs text-[var(--color-text-muted)] mb-2"
        style="font-family: var(--font-label)"
      >
        <span>{{ formatSize(video.filesize) }}</span>
        <span v-if="video.width && video.height">{{ video.width }}x{{ video.height }}</span>
        <StatusBadge :status="video.status" />
      </div>

      <!-- 標籤 -->
      <div v-if="video.tags.length" class="flex flex-wrap gap-1">
        <BaseBadge
          v-for="tag in video.tags.slice(0, 4)"
          :key="tag.id"
          :color="tag.color || 'var(--color-primary-400)'"
        >
          {{ tag.label }}
        </BaseBadge>
        <span
          v-if="video.tags.length > 4"
          class="text-xs text-[var(--color-text-muted)] self-center"
          style="font-family: var(--font-label)"
        >
          +{{ video.tags.length - 4 }}
        </span>
      </div>
    </div>
  </RouterLink>
</template>

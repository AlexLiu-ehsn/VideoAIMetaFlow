<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useVideoStore } from '@/stores/video'
import { subscribeAnalysisStatus } from '@/api/videos'
import VideoCard from '@/components/video/VideoCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const videoStore = useVideoStore()
const statusFilter = ref<string | undefined>(undefined)

// 追蹤目前所有的 SSE 訂閱（key: video_id）
const activeSSE = new Map<string, () => void>()

function subscribeAnalyzingVideos() {
  const analyzingStatuses = new Set(['analyzing', 'uploading_to_gemini'])

  for (const video of videoStore.videos) {
    if (!analyzingStatuses.has(video.status) || activeSSE.has(video.id)) continue

    const unsubscribe = subscribeAnalysisStatus(video.id, (data) => {
      videoStore.updateVideoStatus(video.id, data.status)
      if (data.status === 'completed' || data.status === 'failed') {
        activeSSE.get(video.id)?.()
        activeSSE.delete(video.id)
        // 重新整理列表以取得最新標籤等資訊
        videoStore.loadVideos(videoStore.page, statusFilter.value)
      }
    })
    activeSSE.set(video.id, unsubscribe)
  }
}

function cleanupSSE() {
  for (const unsubscribe of activeSSE.values()) unsubscribe()
  activeSSE.clear()
}

onMounted(() => {
  videoStore.loadVideos()
})

onUnmounted(() => {
  cleanupSSE()
})

// 每次影片列表更新時，訂閱新的分析中影片
watch(() => videoStore.videos, subscribeAnalyzingVideos, { deep: false })

async function onFilterChange(status: string | undefined) {
  statusFilter.value = status
  cleanupSSE()
  await videoStore.loadVideos(1, status)
}

async function onPageChange(page: number) {
  cleanupSSE()
  await videoStore.loadVideos(page, statusFilter.value)
}

const filters = [
  { label: '全部', value: undefined },
  { label: '已完成', value: 'completed' },
  { label: '分析中', value: 'analyzing' },
  { label: '等待中', value: 'pending' },
  { label: '失敗', value: 'failed' },
]
</script>

<template>
  <div>
    <!-- 頁面標題 -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1
          class="text-2xl font-bold text-[var(--color-primary-400)] uppercase tracking-[0.12em]"
          style="font-family: var(--font-heading)"
        >
          <span class="text-[var(--color-text-primary)]">[</span>
          影片庫
          <span class="text-[var(--color-text-primary)]">]</span>
        </h1>
        <p class="text-sm text-[var(--color-text-muted)] mt-1" style="font-family: var(--font-label)">
          <span class="text-[var(--color-primary-400)]">$</span> 共 {{ videoStore.total }} 部影片
        </p>
      </div>
      <RouterLink to="/upload">
        <BaseButton variant="primary">上傳影片</BaseButton>
      </RouterLink>
    </div>

    <!-- 篩選列 -->
    <div class="flex flex-wrap gap-2 mb-6">
      <button
        v-for="filter in filters"
        :key="String(filter.value)"
        class="px-3 py-1.5 text-xs uppercase tracking-[0.08em] transition-all duration-200"
        :class="
          statusFilter === filter.value
            ? 'bg-[var(--color-primary-400)] text-[var(--color-surface-alt)] shadow-[var(--shadow-sm)]'
            : 'bg-[var(--color-surface)] text-[var(--color-text-muted)] border border-[var(--color-border)] hover:border-[rgba(0,255,136,0.3)] hover:text-[var(--color-primary-400)]'
        "
        style="clip-path: var(--chamfer-sm); font-family: var(--font-label)"
        @click="onFilterChange(filter.value)"
      >
        {{ filter.label }}
      </button>
    </div>

    <!-- 載入中 -->
    <div v-if="videoStore.loading" class="flex flex-col items-center py-16 gap-3">
      <div class="w-8 h-8 border-2 border-[var(--color-primary-400)] border-t-transparent rounded-full animate-spin" />
      <span class="text-xs text-[var(--color-text-muted)] uppercase tracking-widest" style="font-family: var(--font-label)">
        載入中<span class="terminal-cursor" />
      </span>
    </div>

    <!-- 空狀態 -->
    <EmptyState
      v-else-if="videoStore.videos.length === 0"
      title="尚無影片"
      description="上傳你的第一部影片，開始自動分析"
    >
      <RouterLink to="/upload">
        <BaseButton variant="primary">上傳影片</BaseButton>
      </RouterLink>
    </EmptyState>

    <!-- 影片網格 -->
    <div
      v-else
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
    >
      <VideoCard
        v-for="video in videoStore.videos"
        :key="video.id"
        :video="video"
      />
    </div>

    <!-- 分頁 -->
    <div
      v-if="videoStore.total > videoStore.pageSize"
      class="flex justify-center gap-2 mt-8"
    >
      <button
        v-for="p in Math.ceil(videoStore.total / videoStore.pageSize)"
        :key="p"
        class="w-9 h-9 text-sm font-medium transition-all duration-200"
        :class="
          videoStore.page === p
            ? 'bg-[var(--color-primary-400)] text-[var(--color-surface-alt)] shadow-[var(--shadow-sm)]'
            : 'bg-[var(--color-surface)] text-[var(--color-text-muted)] border border-[var(--color-border)] hover:border-[rgba(0,255,136,0.3)] hover:text-[var(--color-primary-400)]'
        "
        style="clip-path: var(--chamfer-sm); font-family: var(--font-label)"
        @click="onPageChange(p)"
      >
        {{ p }}
      </button>
    </div>
  </div>
</template>

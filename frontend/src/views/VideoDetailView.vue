<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useVideoStore } from '@/stores/video'
import { getVideoStreamUrl, triggerAnalysis, subscribeAnalysisStatus } from '@/api/videos'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseBadge from '@/components/common/BaseBadge.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import ExportButton from '@/components/common/ExportButton.vue'

const route = useRoute()
const router = useRouter()
const videoStore = useVideoStore()
const videoRef = ref<HTMLVideoElement>()
const currentTime = ref(0)
const analysisStep = ref<string | null>(null)
const analyzing = ref(false)

const id = route.params.id as string
let unsubscribeSSE: (() => void) | null = null

onMounted(() => {
  videoStore.loadVideoDetail(id)
})

onUnmounted(() => {
  unsubscribeSSE?.()
})

watch(
  () => videoStore.currentVideo?.status,
  (status) => {
    if (status === 'analyzing' || status === 'uploading_to_gemini') {
      startSSE()
    }
  },
  { immediate: true },
)

function startSSE() {
  if (unsubscribeSSE) return
  analyzing.value = true
  unsubscribeSSE = subscribeAnalysisStatus(id, (data) => {
    analysisStep.value = data.step
    if (data.status === 'completed' || data.status === 'failed') {
      analyzing.value = false
      unsubscribeSSE?.()
      unsubscribeSSE = null
      videoStore.loadVideoDetail(id)
    }
  })
}

async function handleStartAnalysis() {
  analyzing.value = true
  await triggerAnalysis(id)
  startSSE()
}

function seekTo(time: number) {
  if (videoRef.value) {
    videoRef.value.currentTime = time
    videoRef.value.play()
  }
}

function onTimeUpdate() {
  if (videoRef.value) {
    currentTime.value = videoRef.value.currentTime
  }
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

async function handleDelete() {
  if (!confirm('確定要刪除此影片？')) return
  await videoStore.removeVideo(id)
  router.push('/')
}

const critiqueTypeConfig: Record<string, { label: string; color: string }> = {
  strength: { label: '優點', color: 'var(--color-success)' },
  weakness: { label: '待改善', color: 'var(--color-error)' },
  suggestion: { label: '建議', color: 'var(--color-tertiary)' },
  highlight: { label: '亮點', color: 'var(--color-accent-400)' },
}

const stepLabels: Record<string, string> = {
  upload: '上傳至 Gemini',
  analyzing: 'AI 分析中',
  embedding: '產生向量索引',
  indexing: '建立搜尋索引',
}

function formatElapsed(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}m ${s}s`
}
</script>

<template>
  <!-- 載入中 -->
  <div v-if="videoStore.loading" class="flex flex-col items-center py-16 gap-3">
    <div class="w-8 h-8 border-2 border-[var(--color-primary-400)] border-t-transparent rounded-full animate-spin" />
    <span class="text-xs text-[var(--color-text-muted)] uppercase tracking-widest" style="font-family: var(--font-label)">
      載入中<span class="terminal-cursor" />
    </span>
  </div>

  <div v-else-if="videoStore.currentVideo" class="space-y-6">
    <!-- 返回 + 標題 -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div class="flex items-center gap-3">
        <button
          class="p-2 text-[var(--color-text-muted)] hover:text-[var(--color-primary-400)] transition-colors"
          @click="router.back()"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div>
          <h1 class="text-xl font-bold text-[var(--color-text-primary)]">
            {{ videoStore.currentVideo.filename }}
          </h1>
          <div class="flex items-center gap-2 text-sm text-[var(--color-text-muted)] mt-0.5" style="font-family: var(--font-label)">
            <span>{{ formatSize(videoStore.currentVideo.filesize) }}</span>
            <span v-if="videoStore.currentVideo.width">
              {{ videoStore.currentVideo.width }}x{{ videoStore.currentVideo.height }}
            </span>
            <StatusBadge :status="videoStore.currentVideo.status" />
            <span
              v-if="videoStore.currentVideo.analysis_duration"
              class="text-xs text-[var(--color-tertiary)]"
              :title="`分析耗時 ${formatElapsed(Math.round(videoStore.currentVideo.analysis_duration))}`"
            >
              ⏱ {{ formatElapsed(Math.round(videoStore.currentVideo.analysis_duration)) }}
            </span>
          </div>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <ExportButton
          v-if="videoStore.currentVideo.status === 'completed'"
          :video-ids="[id]"
        />
        <BaseButton variant="danger" size="sm" @click="handleDelete">刪除</BaseButton>
      </div>
    </div>

    <!-- 主要內容區 -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
      <!-- 左側：影片播放器 -->
      <div class="xl:col-span-2 space-y-1">
        <!-- 播放器 -->
        <BaseCard :padding="false">
          <div class="relative aspect-video bg-black overflow-hidden" style="clip-path: var(--chamfer)">
            <video
              ref="videoRef"
              :src="getVideoStreamUrl(id)"
              controls
              class="w-full h-full"
              @timeupdate="onTimeUpdate"
            />
            <!-- HUD 角落裝飾 -->
            <div class="absolute top-2 left-2 w-4 h-4 border-t-2 border-l-2 border-[var(--color-primary-400)] pointer-events-none opacity-60" />
            <div class="absolute top-2 right-2 w-4 h-4 border-t-2 border-r-2 border-[var(--color-primary-400)] pointer-events-none opacity-60" />
            <div class="absolute bottom-12 left-2 w-4 h-4 border-b-2 border-l-2 border-[var(--color-primary-400)] pointer-events-none opacity-60" />
            <div class="absolute bottom-12 right-2 w-4 h-4 border-b-2 border-r-2 border-[var(--color-primary-400)] pointer-events-none opacity-60" />
          </div>
        </BaseCard>

        <!-- 時間軸分段 -->
        <BaseCard v-if="videoStore.currentVideo.segments.length">
          <h2
            class="text-sm font-bold text-[var(--color-primary-400)] mb-4 uppercase tracking-[0.1em]"
            style="font-family: var(--font-heading)"
          >
            <span class="text-[var(--color-text-muted)] mr-1">//</span> 時間軸分析
          </h2>

          <!-- 時間軸視覺化 -->
          <div
            v-if="videoStore.currentVideo.duration"
            class="relative h-8 bg-[var(--color-surface-hover)] mb-4 overflow-hidden cursor-pointer"
            style="clip-path: var(--chamfer-sm)"
          >
            <div
              v-for="segment in videoStore.currentVideo.segments"
              :key="segment.id"
              class="absolute top-0 h-full border-r border-[var(--color-surface)] transition-all duration-200"
              :class="
                currentTime >= segment.start_time && currentTime < segment.end_time
                  ? 'bg-[rgba(0,255,136,0.5)] opacity-100'
                  : 'bg-[rgba(0,255,136,0.2)] opacity-60 hover:opacity-80'
              "
              :style="{
                left: `${(segment.start_time / videoStore.currentVideo.duration!) * 100}%`,
                width: `${((segment.end_time - segment.start_time) / videoStore.currentVideo.duration!) * 100}%`,
              }"
              :title="segment.title || `段落 ${segment.segment_index + 1}`"
              @click="seekTo(segment.start_time)"
            />
            <!-- 播放位置標記 -->
            <div
              class="absolute top-0 w-0.5 h-full bg-[var(--color-error)] z-10"
              :style="{ left: `${(currentTime / videoStore.currentVideo.duration!) * 100}%`, boxShadow: '0 0 6px var(--color-error)' }"
            />
          </div>

          <!-- 分段列表 -->
          <div class="space-y-2">
            <div
              v-for="segment in videoStore.currentVideo.segments"
              :key="segment.id"
              class="p-3 border transition-all duration-200 cursor-pointer"
              :class="
                currentTime >= segment.start_time && currentTime < segment.end_time
                  ? 'border-[var(--color-primary-400)] bg-[rgba(0,255,136,0.05)] shadow-[var(--shadow-sm)]'
                  : 'border-[var(--color-border)] hover:border-[rgba(0,255,136,0.2)] hover:bg-[var(--color-surface-hover)]'
              "
              style="clip-path: var(--chamfer-sm)"
              @click="seekTo(segment.start_time)"
            >
              <div class="flex items-center gap-2 mb-1">
                <span
                  class="text-xs px-1.5 py-0.5 bg-[rgba(0,212,255,0.1)] text-[var(--color-tertiary)]"
                  style="clip-path: var(--chamfer-sm); font-family: var(--font-label)"
                >
                  {{ formatTime(segment.start_time) }} - {{ formatTime(segment.end_time) }}
                </span>
                <span v-if="segment.title" class="text-sm font-medium text-[var(--color-text-primary)]">
                  {{ segment.title }}
                </span>
              </div>
              <p class="text-sm text-[var(--color-text-secondary)]">{{ segment.description }}</p>
              <div v-if="segment.visual_description || segment.audio_description" class="mt-2 space-y-1">
                <p v-if="segment.visual_description" class="text-xs text-[var(--color-text-muted)]">
                  <span class="font-medium text-[var(--color-primary-400)]">畫面：</span>{{ segment.visual_description }}
                </p>
                <p v-if="segment.audio_description" class="text-xs text-[var(--color-text-muted)]">
                  <span class="font-medium text-[var(--color-tertiary)]">語音：</span>{{ segment.audio_description }}
                </p>
              </div>
            </div>
          </div>
        </BaseCard>
      </div>

      <!-- 右側：資訊面板 -->
      <div class="space-y-4">
        <!-- 標籤 -->
        <BaseCard v-if="videoStore.currentVideo.tags.length">
          <h2
            class="text-sm font-bold text-[var(--color-primary-400)] mb-3 uppercase tracking-[0.1em]"
            style="font-family: var(--font-heading)"
          >
            <span class="text-[var(--color-text-muted)] mr-1">//</span> 標籤
          </h2>
          <div class="flex flex-wrap gap-1.5">
            <BaseBadge
              v-for="tag in videoStore.currentVideo.tags"
              :key="tag.id"
              :color="tag.color || 'var(--color-primary-400)'"
            >
              {{ tag.category_label }}：{{ tag.label }}
            </BaseBadge>
          </div>
        </BaseCard>

        <!-- 摘要 -->
        <BaseCard v-if="videoStore.currentVideo.summary">
          <h2
            class="text-sm font-bold text-[var(--color-primary-400)] mb-3 uppercase tracking-[0.1em]"
            style="font-family: var(--font-heading)"
          >
            <span class="text-[var(--color-text-muted)] mr-1">//</span> 摘要
          </h2>
          <p class="text-sm text-[var(--color-text-secondary)] leading-relaxed whitespace-pre-wrap">
            {{ videoStore.currentVideo.summary }}
          </p>
        </BaseCard>

        <!-- 製作人評析 -->
        <BaseCard v-if="videoStore.currentVideo.critique || videoStore.currentVideo.critique_annotations.length">
          <h2
            class="text-sm font-bold text-[var(--color-primary-400)] mb-3 uppercase tracking-[0.1em]"
            style="font-family: var(--font-heading)"
          >
            <span class="text-[var(--color-text-muted)] mr-1">//</span> 製作人評析
          </h2>

          <p
            v-if="videoStore.currentVideo.critique"
            class="text-sm text-[var(--color-text-secondary)] leading-relaxed whitespace-pre-wrap mb-4"
          >
            {{ videoStore.currentVideo.critique }}
          </p>

          <div v-if="videoStore.currentVideo.critique_annotations.length" class="space-y-2">
            <div
              v-for="annotation in videoStore.currentVideo.critique_annotations"
              :key="annotation.id"
              class="flex gap-2 p-2 bg-[var(--color-surface-hover)] hover:bg-[rgba(28,28,46,0.8)] cursor-pointer transition-colors"
              style="clip-path: var(--chamfer-sm)"
              @click="seekTo(annotation.timestamp)"
            >
              <span
                class="text-xs text-[var(--color-tertiary)] shrink-0 pt-0.5"
                style="font-family: var(--font-label)"
              >
                {{ formatTime(annotation.timestamp) }}
              </span>
              <BaseBadge
                :color="critiqueTypeConfig[annotation.type]?.color || 'var(--color-text-muted)'"
                class="shrink-0"
              >
                {{ critiqueTypeConfig[annotation.type]?.label || annotation.type }}
              </BaseBadge>
              <p class="text-xs text-[var(--color-text-secondary)] min-w-0">
                {{ annotation.comment }}
              </p>
            </div>
          </div>
        </BaseCard>

        <!-- 分析狀態 / 觸發分析 -->
        <BaseCard v-if="analyzing || videoStore.currentVideo.status === 'analyzing' || videoStore.currentVideo.status === 'uploading_to_gemini'">
          <div class="py-4 space-y-3">
            <div class="flex items-center gap-3">
              <div class="w-6 h-6 border-2 border-[var(--color-primary-400)] border-t-transparent rounded-full animate-spin shrink-0" />
              <p class="text-sm font-medium text-[var(--color-primary-400)] uppercase tracking-[0.08em]" style="font-family: var(--font-heading)">
                正在分析影片...
              </p>
            </div>
            <p class="text-xs text-[var(--color-text-muted)]" style="font-family: var(--font-label)">
              <span v-if="analysisStep">{{ stepLabels[analysisStep] || analysisStep }}<span class="terminal-cursor" /></span>
              <span v-else>初始化<span class="terminal-cursor" /></span>
            </p>
          </div>
        </BaseCard>

        <BaseCard v-else-if="videoStore.currentVideo.status === 'pending'">
          <div class="text-center py-4">
            <p class="text-sm text-[var(--color-text-muted)] mb-3">此影片尚未進行分析</p>
            <BaseButton variant="primary" size="sm" @click="handleStartAnalysis">開始分析</BaseButton>
          </div>
        </BaseCard>

        <BaseCard v-else-if="videoStore.currentVideo.status === 'failed'">
          <div class="text-center py-4">
            <p class="text-sm text-[var(--color-error)] mb-1" style="font-family: var(--font-label)">// 分析失敗</p>
            <p v-if="videoStore.currentVideo.error_message" class="text-xs text-[var(--color-text-muted)] mb-3">
              {{ videoStore.currentVideo.error_message }}
            </p>
            <BaseButton variant="primary" size="sm" @click="handleStartAnalysis">重新分析</BaseButton>
          </div>
        </BaseCard>
      </div>
    </div>
  </div>
</template>

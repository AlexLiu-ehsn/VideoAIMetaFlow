<script setup lang="ts">
import { computed } from 'vue'
import { XMarkIcon, FilmIcon } from '@heroicons/vue/24/outline'
import BaseButton from '@/components/common/BaseButton.vue'

interface QueueItem {
  file: File
  id: string
}

interface Props {
  items: QueueItem[]
  uploading: boolean
  progress: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  remove: [id: string]
  upload: []
}>()

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

const totalSize = computed(() =>
  props.items.reduce((sum, item) => sum + item.file.size, 0),
)
</script>

<template>
  <div v-if="items.length" class="space-y-3">
    <div class="flex items-center justify-between">
      <h3
        class="text-sm font-medium text-[var(--color-text-primary)] uppercase tracking-[0.05em]"
        style="font-family: var(--font-label)"
      >
        <span class="text-[var(--color-primary-400)] mr-1">//</span>
        已選擇 {{ items.length }} 個檔案（{{ formatSize(totalSize) }}）
      </h3>
      <BaseButton
        v-if="!uploading"
        variant="primary"
        size="sm"
        @click="emit('upload')"
      >
        開始上傳
      </BaseButton>
    </div>

    <!-- 上傳進度條 -->
    <div v-if="uploading" class="w-full h-1 bg-[var(--color-surface-hover)] overflow-hidden" style="clip-path: var(--chamfer-sm)">
      <div
        class="h-full bg-[var(--color-primary-400)] transition-all duration-300"
        :style="{ width: `${progress}%`, boxShadow: '0 0 8px var(--color-primary-400)' }"
      />
    </div>

    <!-- 檔案列表 -->
    <ul class="space-y-2">
      <li
        v-for="item in items"
        :key="item.id"
        class="flex items-center gap-3 p-3 bg-[var(--color-surface)] border border-[var(--color-border)] transition-all hover:border-[rgba(0,255,136,0.2)]"
        style="clip-path: var(--chamfer-sm)"
      >
        <FilmIcon class="w-8 h-8 text-[var(--color-primary-400)] shrink-0 opacity-60" />
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-[var(--color-text-primary)] truncate">
            {{ item.file.name }}
          </p>
          <p class="text-xs text-[var(--color-text-muted)]" style="font-family: var(--font-label)">
            {{ formatSize(item.file.size) }}
          </p>
        </div>
        <button
          v-if="!uploading"
          class="p-1 text-[var(--color-text-muted)] hover:text-[var(--color-error)] transition-colors"
          @click="emit('remove', item.id)"
        >
          <XMarkIcon class="w-5 h-5" />
        </button>
      </li>
    </ul>
  </div>
</template>

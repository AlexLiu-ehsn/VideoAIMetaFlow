<script setup lang="ts">
import { ref } from 'vue'
import { ArrowUpTrayIcon } from '@heroicons/vue/24/outline'

const emit = defineEmits<{
  filesSelected: [files: File[]]
}>()

const dragOver = ref(false)
const fileInput = ref<HTMLInputElement>()

function handleDrop(e: DragEvent) {
  dragOver.value = false
  const files = Array.from(e.dataTransfer?.files || []).filter((f) =>
    f.type.startsWith('video/'),
  )
  if (files.length) emit('filesSelected', files)
}

function handleFileInput(e: Event) {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files || []).filter((f) =>
    f.type.startsWith('video/'),
  )
  if (files.length) emit('filesSelected', files)
  input.value = ''
}

function openFilePicker() {
  fileInput.value?.click()
}
</script>

<template>
  <div
    class="relative border-2 border-dashed p-8 sm:p-12 text-center transition-all duration-300 cursor-pointer"
    :class="
      dragOver
        ? 'border-[var(--color-primary-400)] bg-[rgba(0,255,136,0.05)] shadow-[var(--shadow-md)]'
        : 'border-[var(--color-border)] hover:border-[rgba(0,255,136,0.3)] hover:bg-[var(--color-surface-hover)]'
    "
    style="clip-path: var(--chamfer)"
    @dragover.prevent="dragOver = true"
    @dragleave.prevent="dragOver = false"
    @drop.prevent="handleDrop"
    @click="openFilePicker"
  >
    <input
      ref="fileInput"
      type="file"
      accept="video/*"
      multiple
      class="hidden"
      @change="handleFileInput"
    />

    <!-- 電路板裝飾角落 -->
    <div class="absolute top-2 left-2 w-5 h-5 border-t-2 border-l-2 border-[var(--color-primary-400)] opacity-50" />
    <div class="absolute top-2 right-2 w-5 h-5 border-t-2 border-r-2 border-[var(--color-primary-400)] opacity-50" />
    <div class="absolute bottom-2 left-2 w-5 h-5 border-b-2 border-l-2 border-[var(--color-primary-400)] opacity-50" />
    <div class="absolute bottom-2 right-2 w-5 h-5 border-b-2 border-r-2 border-[var(--color-primary-400)] opacity-50" />

    <ArrowUpTrayIcon
      class="w-12 h-12 mx-auto mb-4 transition-colors"
      :class="
        dragOver
          ? 'text-[var(--color-primary-400)] drop-shadow-[0_0_8px_rgba(0,255,136,0.6)]'
          : 'text-[var(--color-text-muted)]'
      "
    />

    <p
      class="text-base font-bold text-[var(--color-text-primary)] mb-1 uppercase tracking-[0.08em]"
      style="font-family: var(--font-heading)"
    >
      拖放影片至此處
    </p>
    <p class="text-sm text-[var(--color-text-muted)]">
      或點擊選擇檔案 — 支援 MP4、MOV、AVI、MKV 等格式
    </p>
    <p class="text-xs text-[var(--color-primary-400)] mt-2 opacity-70" style="font-family: var(--font-label)">
      // 可同時上傳多個檔案
    </p>
  </div>
</template>

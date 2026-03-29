<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useVideoStore } from '@/stores/video'
import DropZone from '@/components/upload/DropZone.vue'
import UploadQueue from '@/components/upload/UploadQueue.vue'
import BaseCard from '@/components/common/BaseCard.vue'

const router = useRouter()
const videoStore = useVideoStore()

interface QueueItem {
  file: File
  id: string
}

const queue = ref<QueueItem[]>([])
let idCounter = 0

function onFilesSelected(files: File[]) {
  for (const file of files) {
    queue.value.push({ file, id: `file-${idCounter++}` })
  }
}

function removeFromQueue(id: string) {
  queue.value = queue.value.filter((item) => item.id !== id)
}

async function startUpload() {
  if (queue.value.length === 0) return

  const files = queue.value.map((item) => item.file)
  try {
    await videoStore.upload(files)
    queue.value = []
    router.push('/')
  } catch (err) {
    console.error('上傳失敗:', err)
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <h1
      class="text-2xl font-bold text-[var(--color-primary-400)] mb-6 uppercase tracking-[0.12em]"
      style="font-family: var(--font-heading)"
    >
      <span class="text-[var(--color-text-primary)]">[</span>
      上傳影片
      <span class="text-[var(--color-text-primary)]">]</span>
    </h1>

    <BaseCard>
      <DropZone @files-selected="onFilesSelected" />

      <div class="mt-6">
        <UploadQueue
          :items="queue"
          :uploading="videoStore.uploading"
          :progress="videoStore.uploadProgress"
          @remove="removeFromQueue"
          @upload="startUpload"
        />
      </div>
    </BaseCard>
  </div>
</template>

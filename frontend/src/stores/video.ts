import { defineStore } from 'pinia'
import { ref } from 'vue'

import type { VideoDetail, VideoSummary } from '@/types'
import { deleteVideo, fetchVideoDetail, fetchVideos, uploadVideos } from '@/api/videos'

export const useVideoStore = defineStore('video', () => {
  const videos = ref<VideoSummary[]>([])
  const currentVideo = ref<VideoDetail | null>(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const uploading = ref(false)
  const uploadProgress = ref(0)
  const error = ref<string | null>(null)

  async function loadVideos(p = 1, status?: string) {
    loading.value = true
    error.value = null
    try {
      const res = await fetchVideos(p, pageSize.value, status)
      videos.value = res.items
      total.value = res.total
      page.value = res.page
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      error.value = msg
      console.error('[loadVideos] 取得影片列表失敗:', err)
    } finally {
      loading.value = false
    }
  }

  async function loadVideoDetail(id: string) {
    loading.value = true
    try {
      currentVideo.value = await fetchVideoDetail(id)
    } finally {
      loading.value = false
    }
  }

  async function upload(files: File[]) {
    uploading.value = true
    uploadProgress.value = 0
    try {
      const results = await uploadVideos(files, (percent) => {
        uploadProgress.value = percent
      })
      return results
    } finally {
      uploading.value = false
    }
  }

  async function removeVideo(id: string) {
    await deleteVideo(id)
    videos.value = videos.value.filter((v) => v.id !== id)
    total.value = Math.max(0, total.value - 1)
  }

  /** 更新列表中單一影片的狀態（供 SSE 即時更新使用） */
  function updateVideoStatus(id: string, status: string) {
    const video = videos.value.find((v) => v.id === id)
    if (video) {
      video.status = status as import('@/types').VideoStatus
    }
  }

  return {
    videos,
    currentVideo,
    total,
    page,
    pageSize,
    loading,
    error,
    uploading,
    uploadProgress,
    loadVideos,
    loadVideoDetail,
    upload,
    removeVideo,
    updateVideoStatus,
  }
})

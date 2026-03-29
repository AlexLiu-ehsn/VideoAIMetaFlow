import type { UploadResponse, VideoDetail, VideoListResponse } from '@/types'
import apiClient from './client'

export async function fetchVideos(
  page = 1,
  pageSize = 20,
  status?: string,
): Promise<VideoListResponse> {
  const params: Record<string, string | number> = { page, page_size: pageSize }
  if (status) params.status = status
  const { data } = await apiClient.get<VideoListResponse>('/videos', { params })
  return data
}

export async function fetchVideoDetail(id: string): Promise<VideoDetail> {
  const { data } = await apiClient.get<VideoDetail>(`/videos/${id}`)
  return data
}

export async function uploadVideos(
  files: File[],
  onProgress?: (percent: number) => void,
): Promise<UploadResponse[]> {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))

  const { data } = await apiClient.post<UploadResponse[]>('/videos/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    },
  })
  return data
}

export async function deleteVideo(id: string): Promise<void> {
  await apiClient.delete(`/videos/${id}`)
}

export function getVideoStreamUrl(id: string): string {
  return `/api/v1/videos/${id}/stream`
}

export function getThumbnailUrl(id: string): string {
  return `/api/v1/videos/${id}/thumbnail`
}

export async function triggerAnalysis(id: string): Promise<void> {
  await apiClient.post(`/analysis/videos/${id}/analyze`)
}

export function subscribeAnalysisStatus(
  videoId: string,
  onStatus: (data: { status: string; step: string | null; elapsed_seconds: number | null; message: string | null }) => void,
): () => void {
  const eventSource = new EventSource(`/api/v1/analysis/videos/${videoId}/status`)

  eventSource.addEventListener('status', (event) => {
    const data = JSON.parse(event.data)
    onStatus(data)
  })

  eventSource.onerror = () => {
    eventSource.close()
  }

  return () => eventSource.close()
}

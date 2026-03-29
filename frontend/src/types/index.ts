// ===== 影片相關型別 =====

export interface Tag {
  id: number
  name: string
  label: string
  category_name: string
  category_label: string
  color: string | null
}

export interface Segment {
  id: string
  start_time: number
  end_time: number
  title: string | null
  description: string
  visual_description: string | null
  audio_description: string | null
  segment_index: number
}

export interface CritiqueAnnotation {
  id: string
  timestamp: number
  end_time: number | null
  type: 'strength' | 'weakness' | 'suggestion' | 'highlight'
  comment: string
  severity: 'info' | 'minor' | 'major'
}

export interface VideoSummary {
  id: string
  filename: string
  filesize: number
  duration: number | null
  width: number | null
  height: number | null
  thumbnail: string | null
  status: VideoStatus
  created_at: string
  tags: Tag[]
}

export interface VideoDetail extends VideoSummary {
  fps: number | null
  mime_type: string
  summary: string | null
  critique: string | null
  error_message: string | null
  analyzed_at: string | null
  analysis_duration: number | null
  segments: Segment[]
  critique_annotations: CritiqueAnnotation[]
}

export type VideoStatus = 'pending' | 'uploading_to_gemini' | 'analyzing' | 'completed' | 'failed'

export interface VideoListResponse {
  items: VideoSummary[]
  total: number
  page: number
  page_size: number
}

export interface UploadResponse {
  video_id: string
  filename: string
  status: string
}

// ===== 搜尋相關型別 =====

export interface TagFilter {
  category: string
  values: string[]
}

export interface SearchRequest {
  query: string
  mode: 'hybrid' | 'semantic' | 'keyword'
  tag_filters: TagFilter[]
  search_scope: 'videos' | 'segments' | 'both'
  limit: number
  offset: number
}

export interface SearchResultItem {
  type: 'video' | 'segment'
  video_id: string
  video_title: string
  thumbnail: string | null
  score: number
  segment: {
    id: string
    start_time: number
    end_time: number
    description: string
  } | null
  highlight: string | null
}

export interface SearchResponse {
  results: SearchResultItem[]
  total: number
}

// ===== 標籤相關型別 =====

export interface TagCategory {
  id: number
  name: string
  label: string
  color: string | null
  tag_count: number
}

export interface TagWithCount extends Tag {
  video_count: number
}

// ===== 分析相關型別 =====

export interface AnalysisStatus {
  video_id: string
  status: string
  step: string | null
  progress: number | null
  message: string | null
}

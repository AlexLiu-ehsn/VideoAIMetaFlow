import type { SearchRequest, SearchResponse, TagCategory, TagWithCount } from '@/types'
import apiClient from './client'

export async function search(request: SearchRequest): Promise<SearchResponse> {
  const { data } = await apiClient.post<SearchResponse>('/search', request)
  return data
}

export async function fetchTagCategories(): Promise<TagCategory[]> {
  const { data } = await apiClient.get<TagCategory[]>('/tags/categories')
  return data
}

export async function fetchTags(category?: string): Promise<TagWithCount[]> {
  const params: Record<string, string> = {}
  if (category) params.category = category
  const { data } = await apiClient.get<TagWithCount[]>('/tags', { params })
  return data
}

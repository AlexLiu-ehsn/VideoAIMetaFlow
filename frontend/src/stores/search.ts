import { defineStore } from 'pinia'
import { ref } from 'vue'

import type { SearchResultItem, TagCategory, TagFilter, TagWithCount } from '@/types'
import { fetchTagCategories, fetchTags, search } from '@/api/search'

export const useSearchStore = defineStore('search', () => {
  const query = ref('')
  const mode = ref<'hybrid' | 'semantic' | 'keyword'>('hybrid')
  const tagFilters = ref<TagFilter[]>([])
  const searchScope = ref<'videos' | 'segments' | 'both'>('both')
  const results = ref<SearchResultItem[]>([])
  const totalResults = ref(0)
  const searching = ref(false)

  const categories = ref<TagCategory[]>([])
  const allTags = ref<TagWithCount[]>([])

  async function performSearch(offset = 0) {
    searching.value = true
    try {
      const res = await search({
        query: query.value,
        mode: mode.value,
        tag_filters: tagFilters.value,
        search_scope: searchScope.value,
        limit: 20,
        offset,
      })
      results.value = res.results
      totalResults.value = res.total
    } finally {
      searching.value = false
    }
  }

  async function loadTagCategories() {
    categories.value = await fetchTagCategories()
  }

  async function loadAllTags() {
    allTags.value = await fetchTags()
  }

  function toggleTagFilter(categoryName: string, tagValue: string) {
    const existing = tagFilters.value.find((f) => f.category === categoryName)
    if (existing) {
      const idx = existing.values.indexOf(tagValue)
      if (idx >= 0) {
        existing.values.splice(idx, 1)
        if (existing.values.length === 0) {
          tagFilters.value = tagFilters.value.filter((f) => f.category !== categoryName)
        }
      } else {
        existing.values.push(tagValue)
      }
    } else {
      tagFilters.value.push({ category: categoryName, values: [tagValue] })
    }
  }

  function clearFilters() {
    tagFilters.value = []
  }

  return {
    query,
    mode,
    tagFilters,
    searchScope,
    results,
    totalResults,
    searching,
    categories,
    allTags,
    performSearch,
    loadTagCategories,
    loadAllTags,
    toggleTagFilter,
    clearFilters,
  }
})

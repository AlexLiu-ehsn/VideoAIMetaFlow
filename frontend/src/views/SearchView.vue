<script setup lang="ts">
import { onMounted } from 'vue'
import { useSearchStore } from '@/stores/search'
import { getThumbnailUrl } from '@/api/videos'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseBadge from '@/components/common/BaseBadge.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const searchStore = useSearchStore()

onMounted(() => {
  searchStore.loadTagCategories()
  searchStore.loadAllTags()
})

function handleSearch() {
  if (searchStore.query.trim()) {
    searchStore.performSearch()
  }
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

const modeOptions = [
  { label: '混合', value: 'hybrid' as const },
  { label: '語意', value: 'semantic' as const },
  { label: '關鍵字', value: 'keyword' as const },
]
</script>

<template>
  <div>
    <h1
      class="text-2xl font-bold text-[var(--color-primary-400)] mb-6 uppercase tracking-[0.12em]"
      style="font-family: var(--font-heading)"
    >
      <span class="text-[var(--color-text-primary)]">[</span>
      搜尋影片
      <span class="text-[var(--color-text-primary)]">]</span>
    </h1>

    <!-- 搜尋列 -->
    <BaseCard class="mb-6">
      <div class="flex flex-col sm:flex-row gap-3">
        <div class="flex-1 relative">
          <input
            v-model="searchStore.query"
            type="text"
            placeholder="輸入搜尋關鍵字或描述，例如「開箱的那個瞬間」..."
            class="w-full px-4 py-2.5 pr-10 bg-[var(--color-surface-alt)] border border-[var(--color-border)] text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary-400)] focus:shadow-[var(--shadow-sm)] transition-all"
            style="clip-path: var(--chamfer-sm)"
            @keydown.enter="handleSearch"
          />
          <svg
            class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-muted)]"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
        </div>

        <!-- 搜尋模式 -->
        <div class="flex gap-1 bg-[var(--color-surface-alt)] p-1" style="clip-path: var(--chamfer-sm)">
          <button
            v-for="opt in modeOptions"
            :key="opt.value"
            class="px-3 py-1.5 text-xs font-medium uppercase tracking-[0.08em] transition-all duration-200"
            :class="
              searchStore.mode === opt.value
                ? 'bg-[var(--color-surface)] text-[var(--color-primary-400)] shadow-[var(--shadow-sm)]'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'
            "
            style="clip-path: var(--chamfer-sm); font-family: var(--font-label)"
            @click="searchStore.mode = opt.value"
          >
            {{ opt.label }}
          </button>
        </div>

        <BaseButton variant="primary" @click="handleSearch">搜尋</BaseButton>
      </div>
    </BaseCard>

    <!-- 內容區：桌面左右/手機上下 -->
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <!-- 左側：標籤篩選 -->
      <aside class="lg:col-span-1">
        <BaseCard>
          <h3
            class="text-sm font-bold text-[var(--color-primary-400)] mb-3 uppercase tracking-[0.1em]"
            style="font-family: var(--font-heading)"
          >
            <span class="text-[var(--color-text-muted)] mr-1">//</span> 標籤篩選
          </h3>
          <div v-if="searchStore.categories.length" class="space-y-4">
            <div v-for="cat in searchStore.categories" :key="cat.id">
              <h4 class="text-xs font-medium text-[var(--color-text-muted)] uppercase mb-2" style="font-family: var(--font-label)">
                {{ cat.label }}
              </h4>
              <div class="flex flex-wrap gap-1">
                <button
                  v-for="tag in searchStore.allTags.filter((t) => t.category_name === cat.name)"
                  :key="tag.id"
                  class="px-2 py-1 text-xs border transition-all duration-200"
                  :class="
                    searchStore.tagFilters.some(
                      (f) => f.category === cat.name && f.values.includes(tag.name),
                    )
                      ? 'border-[var(--color-primary-400)] bg-[rgba(0,255,136,0.1)] text-[var(--color-primary-400)]'
                      : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-[rgba(0,255,136,0.2)] hover:text-[var(--color-text-secondary)]'
                  "
                  style="clip-path: var(--chamfer-sm); font-family: var(--font-label)"
                  @click="searchStore.toggleTagFilter(cat.name, tag.name)"
                >
                  {{ tag.label }}
                  <span class="ml-1 opacity-50">{{ tag.video_count }}</span>
                </button>
              </div>
            </div>
          </div>
          <p v-else class="text-sm text-[var(--color-text-muted)]">尚無標籤</p>
        </BaseCard>
      </aside>

      <!-- 右側：搜尋結果 -->
      <div class="lg:col-span-3">
        <!-- 載入中 -->
        <div v-if="searchStore.searching" class="flex flex-col items-center py-16 gap-3">
          <div class="w-8 h-8 border-2 border-[var(--color-primary-400)] border-t-transparent rounded-full animate-spin" />
          <span class="text-xs text-[var(--color-text-muted)] uppercase tracking-widest" style="font-family: var(--font-label)">
            搜尋中<span class="terminal-cursor" />
          </span>
        </div>

        <!-- 空狀態 -->
        <EmptyState
          v-else-if="searchStore.results.length === 0 && searchStore.query"
          title="未找到結果"
          description="嘗試調整搜尋關鍵字或篩選條件"
        />

        <EmptyState
          v-else-if="searchStore.results.length === 0"
          title="開始搜尋"
          description="輸入自然語言描述或關鍵字來搜尋影片內容"
        />

        <!-- 結果列表 -->
        <div v-else class="space-y-3">
          <p class="text-sm text-[var(--color-text-muted)] mb-2" style="font-family: var(--font-label)">
            <span class="text-[var(--color-primary-400)]">$</span> 找到 {{ searchStore.totalResults }} 個結果
          </p>

          <RouterLink
            v-for="result in searchStore.results"
            :key="`${result.video_id}-${result.segment?.id || 'video'}`"
            :to="
              result.segment
                ? `/videos/${result.video_id}?t=${result.segment.start_time}`
                : `/videos/${result.video_id}`
            "
            class="block"
          >
            <BaseCard hoverable>
              <div class="flex gap-4">
                <!-- 縮圖 -->
                <div class="w-32 sm:w-40 shrink-0 aspect-video bg-[var(--color-surface-hover)] overflow-hidden" style="clip-path: var(--chamfer-sm)">
                  <img
                    v-if="result.thumbnail"
                    :src="getThumbnailUrl(result.video_id)"
                    class="w-full h-full object-cover"
                  />
                </div>

                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <BaseBadge
                      :color="result.type === 'segment' ? 'var(--color-accent-400)' : 'var(--color-primary-400)'"
                    >
                      {{ result.type === 'segment' ? '片段' : '影片' }}
                    </BaseBadge>
                    <span
                      v-if="result.segment"
                      class="text-xs text-[var(--color-tertiary)]"
                      style="font-family: var(--font-label)"
                    >
                      {{ formatTime(result.segment.start_time) }} - {{ formatTime(result.segment.end_time) }}
                    </span>
                  </div>

                  <h3 class="text-sm font-medium text-[var(--color-text-primary)] truncate">
                    {{ result.video_title }}
                  </h3>

                  <p
                    v-if="result.highlight || result.segment?.description"
                    class="text-xs text-[var(--color-text-secondary)] line-clamp-2 mt-1"
                  >
                    {{ result.highlight || result.segment?.description }}
                  </p>
                </div>
              </div>
            </BaseCard>
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

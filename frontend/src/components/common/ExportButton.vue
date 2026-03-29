<script setup lang="ts">
import { ref } from 'vue'
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import { ArrowDownTrayIcon } from '@heroicons/vue/24/outline'

interface Props {
  videoIds: string[]
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
})

const loading = ref(false)

const formats = [
  { label: 'JSON', value: 'json', description: '完整結構化資料' },
  { label: 'CSV', value: 'csv', description: '扁平化表格（一行一分段）' },
  { label: 'XLSX', value: 'xlsx', description: 'Excel 多工作表' },
]

async function handleExport(format: string) {
  if (props.videoIds.length === 0) return
  loading.value = true

  try {
    let url: string
    let fetchOptions: RequestInit = {}

    if (props.videoIds.length === 1) {
      url = `/api/v1/videos/${props.videoIds[0]}/export?format=${format}`
    } else {
      url = '/api/v1/export/batch'
      fetchOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_ids: props.videoIds, format }),
      }
    }

    const response = await fetch(url, fetchOptions)
    if (!response.ok) throw new Error('匯出失敗')

    const blob = await response.blob()
    const downloadUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = `video_metadata.${format}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(downloadUrl)
  } catch (err) {
    console.error('匯出失敗:', err)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <Menu as="div" class="relative inline-block text-left">
    <MenuButton
      class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium uppercase tracking-[0.08em] border border-[var(--color-border)] text-[var(--color-text-secondary)] bg-[var(--color-surface)] hover:border-[rgba(0,255,136,0.3)] hover:text-[var(--color-primary-400)] hover:shadow-[var(--shadow-sm)] transition-all duration-200 disabled:opacity-50"
      :disabled="disabled || loading || videoIds.length === 0"
      style="clip-path: var(--chamfer-sm); font-family: var(--font-label)"
    >
      <ArrowDownTrayIcon class="w-4 h-4" />
      <span>匯出</span>
      <span
        v-if="loading"
        class="animate-spin w-3 h-3 border border-current border-t-transparent rounded-full"
      />
    </MenuButton>

    <transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <MenuItems
        class="absolute right-0 z-10 mt-2 w-56 origin-top-right bg-[var(--color-surface)] border border-[var(--color-primary-400)] shadow-[var(--shadow-md)] focus:outline-none overflow-hidden"
        style="clip-path: var(--chamfer)"
      >
        <div class="py-1">
          <MenuItem v-for="fmt in formats" :key="fmt.value" v-slot="{ active }">
            <button
              class="flex items-center gap-3 w-full px-4 py-3 text-left transition-colors uppercase tracking-[0.08em]"
              :class="active ? 'bg-[rgba(0,255,136,0.1)] text-[var(--color-primary-400)]' : 'text-[var(--color-text-primary)]'"
              style="font-family: var(--font-label)"
              @click="handleExport(fmt.value)"
            >
              <span
                class="text-[var(--color-primary-400)] opacity-0 transition-opacity"
                :class="{ 'opacity-100': active }"
              >&gt;</span>
              <div>
                <span class="text-sm font-medium block">{{ fmt.label }}</span>
                <span class="text-xs text-[var(--color-text-muted)] normal-case tracking-normal">{{ fmt.description }}</span>
              </div>
            </button>
          </MenuItem>
        </div>
      </MenuItems>
    </transition>
  </Menu>
</template>

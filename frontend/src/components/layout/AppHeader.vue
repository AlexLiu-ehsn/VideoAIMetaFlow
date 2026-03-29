<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { Bars3Icon, XMarkIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const mobileMenuOpen = ref(false)

const navItems = [
  { name: '影片庫', to: '/' },
  { name: '上傳', to: '/upload' },
  { name: '搜尋', to: '/search' },
]

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<template>
  <header class="sticky top-0 z-50 bg-[rgba(10,10,15,0.92)] backdrop-blur-[12px] border-b border-[var(--color-border)]">
    <div class="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <RouterLink to="/" class="flex items-center gap-3 shrink-0 group">
          <!-- 六角形 Logo SVG -->
          <svg class="w-9 h-9" viewBox="0 0 36 36" fill="none">
            <path d="M4 8L18 2L32 8V28L18 34L4 28V8Z" stroke="#00ff88" stroke-width="1.5" fill="none"/>
            <path d="M12 14L18 10L24 14V22L18 26L12 22V14Z" fill="rgba(0,255,136,0.19)" stroke="#00ff88" stroke-width="1"/>
            <circle cx="18" cy="18" r="3" fill="#00ff88"/>
          </svg>
          <span
            class="font-[var(--font-heading)] font-extrabold text-xl uppercase tracking-[0.15em] text-[var(--color-primary-400)] glitch-text"
            style="font-family: var(--font-heading)"
          >
            VideoAI MetaFlow
          </span>
        </RouterLink>

        <!-- 桌面導覽 -->
        <nav class="hidden md:flex items-center gap-2">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="px-4 py-2 text-sm uppercase tracking-[0.1em] transition-all duration-200 cyber-clip-sm"
            :class="
              isActive(item.to)
                ? 'bg-[rgba(0,255,136,0.08)] text-[var(--color-primary-400)]'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-primary-400)] hover:bg-[rgba(0,255,136,0.05)]'
            "
            style="font-family: var(--font-label)"
          >
            <span v-if="isActive(item.to)" class="mr-1.5 animate-[blink_1s_step-end_infinite]">&gt;</span>
            {{ item.name }}
          </RouterLink>
        </nav>

        <!-- 系統狀態指示器 -->
        <div class="hidden md:flex items-center gap-2 ml-4 text-xs text-[var(--color-text-muted)]" style="font-family: var(--font-label)">
          <span class="w-2 h-2 bg-[var(--color-primary-400)] rounded-full shadow-[0_0_6px_var(--color-primary-400)] animate-[blink_2s_ease-in-out_infinite]" />
          <span>SYS:ONLINE</span>
        </div>

        <!-- 手機選單按鈕 -->
        <button
          class="md:hidden p-2 text-[var(--color-text-muted)] hover:text-[var(--color-primary-400)] transition-colors"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          <Bars3Icon v-if="!mobileMenuOpen" class="w-6 h-6" />
          <XMarkIcon v-else class="w-6 h-6" />
        </button>
      </div>

      <!-- 手機導覽 -->
      <nav
        v-if="mobileMenuOpen"
        class="md:hidden pb-4 border-t border-[var(--color-border)] pt-2 space-y-1"
      >
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="block px-4 py-3 text-sm uppercase tracking-[0.1em] transition-colors cyber-clip-sm"
          :class="
            isActive(item.to)
              ? 'bg-[rgba(0,255,136,0.08)] text-[var(--color-primary-400)]'
              : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-primary-400)]'
          "
          style="font-family: var(--font-label)"
          @click="mobileMenuOpen = false"
        >
          <span v-if="isActive(item.to)" class="mr-1.5">&gt;</span>
          {{ item.name }}
        </RouterLink>
      </nav>
    </div>
  </header>
</template>

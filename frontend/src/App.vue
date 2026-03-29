<script setup lang="ts">
import AppHeader from '@/components/layout/AppHeader.vue'
</script>

<template>
  <div class="min-h-screen flex flex-col bg-[var(--color-surface-alt)]">
    <AppHeader />
    <main class="flex-1 w-full max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-6 animate-[fadeInUp_0.6s_ease-out]">
      <RouterView />
    </main>
  </div>
</template>

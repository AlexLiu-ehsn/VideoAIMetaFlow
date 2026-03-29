<script setup lang="ts">
interface Props {
  title: string
  description?: string
  icon?: string
}

defineProps<Props>()
</script>

<template>
  <div class="flex flex-col items-center justify-center py-16 text-center">
    <span v-if="icon" class="text-4xl mb-4 opacity-60">{{ icon }}</span>
    <h3
      class="text-lg font-bold text-[var(--color-primary-400)] mb-1 uppercase tracking-[0.1em]"
      style="font-family: var(--font-heading)"
    >
      {{ title }}
    </h3>
    <p v-if="description" class="text-sm text-[var(--color-text-muted)] max-w-md">{{ description }}</p>
    <div class="mt-4">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  color?: string
  variant?: 'solid' | 'outline'
}

withDefaults(defineProps<Props>(), {
  color: 'var(--color-primary-400)',
  variant: 'solid',
})
</script>

<template>
  <span
    class="inline-flex items-center px-2.5 py-1 text-xs font-medium whitespace-nowrap uppercase tracking-[0.08em]"
    style="clip-path: var(--chamfer-sm); font-family: var(--font-label)"
    :style="
      variant === 'solid'
        ? { backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)`, color, border: `1px solid color-mix(in srgb, ${color} 30%, transparent)` }
        : { borderColor: color, color, border: `1px solid ${color}`, background: 'transparent' }
    "
  >
    <slot />
  </span>
</template>

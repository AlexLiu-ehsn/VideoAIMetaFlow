<script setup lang="ts">
interface Props {
  hoverable?: boolean
  padding?: boolean
}

withDefaults(defineProps<Props>(), {
  hoverable: false,
  padding: true,
})
</script>

<template>
  <div
    class="bg-[var(--color-surface)] border border-[var(--color-border)] transition-all duration-300"
    :class="{
      'hover:border-[rgba(0,255,136,0.3)] hover:shadow-[var(--shadow-sm)] cursor-pointer': hoverable,
      'p-4 sm:p-6': padding,
    }"
    style="clip-path: var(--chamfer)"
  >
    <slot />
  </div>
</template>

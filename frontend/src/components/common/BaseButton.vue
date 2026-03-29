<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  loading: false,
  disabled: false,
})

const variantClasses: Record<string, string> = {
  primary:
    'bg-[var(--color-primary-400)] text-[var(--color-surface-alt)] hover:bg-[#33ffaa] shadow-[var(--shadow-md)] hover:shadow-[var(--shadow-lg)]',
  secondary:
    'bg-[var(--color-surface)] text-[var(--color-text-primary)] border border-[var(--color-border)] hover:border-[rgba(0,255,136,0.3)] hover:text-[var(--color-primary-400)]',
  ghost:
    'text-[var(--color-text-muted)] hover:bg-[rgba(0,255,136,0.05)] hover:text-[var(--color-primary-400)]',
  danger:
    'bg-[rgba(255,51,102,0.15)] text-[var(--color-error)] border border-[rgba(255,51,102,0.25)] hover:bg-[rgba(255,51,102,0.25)] hover:shadow-[var(--shadow-neon-error)]',
}

const sizeClasses: Record<string, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
}
</script>

<template>
  <button
    :class="[
      'inline-flex items-center justify-center font-medium uppercase tracking-[0.08em] transition-all duration-200 focus:outline-none focus:ring-1 focus:ring-[var(--color-primary-400)] disabled:opacity-50 disabled:cursor-not-allowed',
      variantClasses[variant],
      sizeClasses[size],
    ]"
    :disabled="disabled || loading"
    style="clip-path: var(--chamfer-sm); font-family: var(--font-label)"
  >
    <svg
      v-if="loading"
      class="animate-spin -ml-1 mr-2 h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
    <slot />
  </button>
</template>

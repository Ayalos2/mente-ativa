<script setup>
defineProps({
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  text: {
    type: String,
    default: ''
  },
  fullScreen: {
    type: Boolean,
    default: false
  }
})

const sizeClasses = {
  sm: 'h-6 w-6 border-2',
  md: 'h-12 w-12 border-4',
  lg: 'h-16 w-16 border-4'
}
</script>

<template>
  <div :class="['flex flex-col items-center justify-center gap-3', fullScreen ? 'fixed inset-0 bg-white/80 backdrop-blur-sm z-50' : 'py-12']">
    <div
      :class="[
        'animate-spin rounded-full border-slate-200 border-t-emerald-600',
        sizeClasses[size]
      ]"
    ></div>
    <p v-if="text" class="text-sm font-medium text-slate-600">{{ text }}</p>
  </div>
</template>
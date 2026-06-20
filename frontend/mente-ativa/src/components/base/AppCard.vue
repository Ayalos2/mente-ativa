<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  },
  padding: {
    type: String,
    default: 'p-6',
    validator: (value) => ['p-4', 'p-6', 'p-8'].includes(value)
  },
  hoverable: {
    type: Boolean,
    default: false
  }
})
</script>

<template>
  <div
    :class="[
      'bg-white rounded-2xl shadow-md border border-slate-200',
      padding,
      hoverable ? 'hover:shadow-lg hover:border-slate-300 transition-all' : ''
    ]"
  >
    <div v-if="title || subtitle" class="mb-4">
      <h3 v-if="title" class="text-xl font-bold text-slate-900">{{ title }}</h3>
      <p v-if="subtitle" class="text-sm text-slate-600 mt-1">{{ subtitle }}</p>
    </div>
    <slot />
  </div>
</template>
<script setup>
defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'danger', 'ghost'].includes(value)
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  disabled: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  type: {
    type: String,
    default: 'button'
  }
})

const emit = defineEmits(['click'])

const handleClick = (event) => {
  emit('click', event)
}

const variantClasses = {
  primary: 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-200',
  secondary: 'bg-slate-900 hover:bg-slate-800 text-white shadow-lg shadow-slate-200',
  danger: 'bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-200',
  ghost: 'bg-transparent hover:bg-slate-100 text-slate-700 border-2 border-slate-200'
}

const sizeClasses = {
  sm: 'px-4 py-2 text-sm rounded-lg',
  md: 'px-6 py-3 text-base rounded-xl',
  lg: 'px-8 py-4 text-lg rounded-2xl'
}
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="[
      'inline-flex items-center justify-center font-bold transition-all',
      'active:scale-95 focus:outline-none focus:ring-4',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      variantClasses[variant],
      sizeClasses[size]
    ]"
    @click="handleClick"
  >
    <span v-if="loading" class="flex items-center gap-2">
      <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <slot name="loading">Carregando...</slot>
    </span>
    <slot v-else />
  </button>
</template>
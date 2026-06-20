<script setup>
defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  },
  label: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: ''
  },
  error: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  required: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const handleInput = (event) => {
  emit('update:modelValue', event.target.value)
}
</script>

<template>
  <div class="w-full">
    <label v-if="label" class="block text-sm font-semibold text-slate-700 mb-2">
      {{ label }}
      <span v-if="required" class="text-red-500 ml-1">*</span>
    </label>
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :class="[
        'w-full px-4 py-3 rounded-xl border transition-all',
        'focus:outline-none focus:ring-4 focus:ring-emerald-300',
        'disabled:bg-slate-100 disabled:cursor-not-allowed',
        error 
          ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200' 
          : 'border-slate-300 bg-white focus:border-emerald-500'
      ]"
      @input="handleInput"
    />
    <p v-if="error" class="mt-2 text-sm font-medium text-red-700">
      {{ error }}
    </p>
  </div>
</template>
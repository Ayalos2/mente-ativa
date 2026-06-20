<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  label: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  },
  metrics: {
    type: Array,
    default: () => []
  },
  route: {
    type: String,
    required: true
  },
  accent: {
    type: String,
    default: 'emerald',
    validator: (value) => ['emerald', 'amber', 'violet', 'blue'].includes(value)
  }
})

const emit = defineEmits(['start'])

const startTest = () => {
  emit('start')
}

const accentClasses = {
  emerald: 'border-emerald-200 hover:border-emerald-400 hover:shadow-emerald-100/50',
  amber: 'border-amber-200 hover:border-amber-400 hover:shadow-amber-100/50',
  violet: 'border-violet-200 hover:border-violet-400 hover:shadow-violet-100/50',
  blue: 'border-blue-200 hover:border-blue-400 hover:shadow-blue-100/50'
}

const buttonClasses = {
  emerald: 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-200',
  amber: 'bg-amber-600 hover:bg-amber-700 shadow-amber-200',
  violet: 'bg-violet-600 hover:bg-violet-700 shadow-violet-200',
  blue: 'bg-blue-600 hover:bg-blue-700 shadow-blue-200'
}
</script>

<template>
  <article
    :class="[
      'rounded-3xl border bg-white p-6 sm:p-7 shadow-sm flex flex-col gap-4 transition-all',
      accentClasses[accent]
    ]"
  >
    <div v-if="label" class="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-black uppercase tracking-[0.2em] text-slate-700 w-fit">
      {{ label }}
    </div>

    <div class="space-y-2">
      <h2 class="text-2xl font-black text-slate-950">{{ title }}</h2>
      <p v-if="description" class="text-slate-600 leading-relaxed">{{ description }}</p>
    </div>

    <div v-if="metrics.length" class="flex flex-wrap gap-2">
      <span 
        v-for="metric in metrics" 
        :key="metric" 
        class="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-700"
      >
        {{ metric }}
      </span>
    </div>

    <button
      @click="startTest"
      class="mt-auto rounded-2xl px-5 py-3 font-black text-white transition-all hover:opacity-90"
      :class="buttonClasses[accent]"
    >
      Iniciar teste
    </button>
  </article>
</template>
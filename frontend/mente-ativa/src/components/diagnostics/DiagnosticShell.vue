<script setup>
import { computed } from 'vue'

const accentClassMap = {
  emerald: 'text-emerald-300',
  amber: 'text-amber-300',
  violet: 'text-violet-300',
}

const props = defineProps({
  eyebrow: {
    type: String,
    default: 'Acompanhamento cognitivo',
  },
  title: {
    type: String,
    required: true,
  },
  subtitle: {
    type: String,
    default: '',
  },
  accent: {
    type: String,
    default: 'emerald',
  },
})

defineEmits(['back', 'dashboard'])

const accentClass = computed(() => accentClassMap[props.accent] || accentClassMap.emerald)
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-50">
    <header class="border-b border-slate-800 bg-slate-950/95 sticky top-0 z-40 backdrop-blur">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-5 flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5">
        <div class="space-y-2">
          <p :class="accentClass + ' text-xs font-black uppercase tracking-[0.35em]'">{{ eyebrow }}</p>
          <h1 class="text-3xl sm:text-4xl font-black tracking-tight text-white">{{ title }}</h1>
          <p v-if="subtitle" class="max-w-4xl text-slate-300 text-base sm:text-lg leading-relaxed">{{ subtitle }}</p>
        </div>

        <div class="flex flex-wrap gap-3">
          <button
            @click="$emit('back')"
            class="rounded-2xl border border-slate-700 bg-slate-900 px-5 py-3 font-bold text-slate-100 hover:bg-slate-800"
          >
            Voltar
          </button>
          <button
            @click="$emit('dashboard')"
            class="rounded-2xl bg-emerald-500 px-5 py-3 font-black text-slate-950 hover:bg-emerald-400"
          >
            Painel de testes
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <slot />
    </main>
  </div>
</template>

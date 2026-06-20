<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

defineProps({
  userName: {
    type: String,
    default: ''
  },
  userRole: {
    type: String,
    default: 'paciente'
  }
})

const navigateTo = (path) => {
  router.push(path)
}
</script>

<template>
  <aside class="w-64 bg-white border-r border-slate-200 min-h-screen p-6">
    <div class="flex items-center gap-3 mb-8">
      <div class="bg-emerald-600 p-2 rounded-lg shadow-md">
        <span class="text-white text-xl">🧠</span>
      </div>
      <span class="text-xl font-bold text-slate-800 tracking-tight">Mente Ativa</span>
    </div>

    <div class="mb-6 p-4 bg-slate-50 rounded-xl">
      <p class="text-sm font-semibold text-slate-900 truncate">{{ userName }}</p>
      <p class="text-xs text-slate-600 mt-1">{{ userRole === 'especialista' ? 'Médico / Especialista' : 'Paciente' }}</p>
    </div>

    <nav class="space-y-1">
      <button
        @click="navigateTo('/profile')"
        class="w-full text-left px-4 py-3 rounded-xl text-sm font-semibold text-slate-700 hover:bg-slate-50 hover:text-emerald-700 transition-colors flex items-center gap-3"
      >
        <span>📊</span>
        Painel
      </button>

      <button
        v-if="userRole === 'especialista'"
        @click="navigateTo('/profile')"
        class="w-full text-left px-4 py-3 rounded-xl text-sm font-semibold text-slate-700 hover:bg-slate-50 hover:text-emerald-700 transition-colors flex items-center gap-3"
      >
        <span>👥</span>
        Pacientes
      </button>

      <button
        @click="navigateTo('/profile/historico')"
        class="w-full text-left px-4 py-3 rounded-xl text-sm font-semibold text-slate-700 hover:bg-slate-50 hover:text-emerald-700 transition-colors flex items-center gap-3"
      >
        <span>📋</span>
        Histórico
      </button>

      <button
        @click="navigateTo('/profile/edit')"
        class="w-full text-left px-4 py-3 rounded-xl text-sm font-semibold text-slate-700 hover:bg-slate-50 hover:text-emerald-700 transition-colors flex items-center gap-3"
      >
        <span>⚙️</span>
        Configurações
      </button>
    </nav>
  </aside>
</template>
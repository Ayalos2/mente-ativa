<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

defineProps({
  showBackButton: {
    type: Boolean,
    default: false
  },
  backRoute: {
    type: String,
    default: '/'
  }
})

const goBack = () => {
  router.push(props.backRoute)
}

const goHome = () => {
  router.push('/')
}
</script>

<template>
  <nav class="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-20 items-center">
        
        <div class="flex items-center gap-3 cursor-pointer" @click="goHome">
          <div class="bg-emerald-600 p-2.5 rounded-xl shadow-md">
            <span class="text-white text-2xl" aria-hidden="true">🧠</span>
          </div>
          <span class="text-2xl font-bold text-slate-800 tracking-tight">Mente Ativa</span>
        </div>

        <div class="flex items-center gap-4">
          <button 
            v-if="showBackButton"
            @click="goBack"
            class="text-slate-500 hover:text-emerald-600 flex items-center gap-2 transition-colors font-medium"
          >
            <span>←</span> Voltar
          </button>
        </div>

      </div>
    </div>
  </nav>
</template>
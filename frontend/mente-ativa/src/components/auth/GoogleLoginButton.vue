<script setup>
import { computed, ref } from 'vue'
import { isFirebaseConfigured } from '../../config/firebase'
import { loginComGoogle } from '../../services/googleAuth'

const emit = defineEmits(['success', 'error'])

const carregando = ref(false)

const textoBotao = computed(() => {
  return carregando.value ? 'Entrando...' : 'Continuar com Google'
})

const entrarComGoogle = async () => {
  if (!isFirebaseConfigured || carregando.value) {
    return
  }

  carregando.value = true

  try {
    const resultado = await loginComGoogle()
    emit('success', resultado)
  } catch (error) {
    emit('error', error)
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <button
    type="button"
    :disabled="!isFirebaseConfigured || carregando"
    @click="entrarComGoogle"
    class="w-full flex items-center justify-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3.5 text-sm font-semibold text-slate-700 shadow-sm transition-all hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-200 disabled:cursor-not-allowed disabled:opacity-60"
  >
    <svg aria-hidden="true" viewBox="0 0 48 48" class="h-5 w-5">
      <path fill="#FFC107" d="M43.6 20.4H42V20H24v8h11.3C33.7 32.8 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.8 1.1 7.9 3l5.7-5.7C34.1 6.1 29.4 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.1-.4-3.6z"/>
      <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15 19 12 24 12c3 0 5.8 1.1 7.9 3l5.7-5.7C34.1 6.1 29.4 4 24 4 16.1 4 9.2 8.5 6.3 14.7z"/>
      <path fill="#4CAF50" d="M24 44c5.3 0 10-2 13.6-5.4l-6.3-5.1C29.1 35.2 26.8 36 24 36c-5.3 0-9.8-3.3-11.5-7.9l-6.5 5C9 39.4 15.9 44 24 44z"/>
      <path fill="#1976D2" d="M43.6 20.4H42V20H24v8h11.3c-1.1 3.2-3.3 5.7-6 7.5l.1-.1 6.3 5.1C35.2 39.3 44 33.5 44 24c0-1.3-.1-2.1-.4-3.6z"/>
    </svg>
    <span>{{ textoBotao }}</span>
  </button>
</template>

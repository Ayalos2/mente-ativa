<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { signOut } from 'firebase/auth'
import { auth } from '../config/firebase'

const router = useRouter()
const userData = ref(null)
const localStorageEnabled = ref(false)
const analyticsSharing = ref(false)
const biometricLock = ref(true)

const isLogged = computed(() => Boolean(userData.value))

onMounted(() => {
  const storedUser = sessionStorage.getItem('userProfile')

  if (storedUser) {
    try {
      userData.value = JSON.parse(storedUser)
    } catch {
      userData.value = null
    }
  }
})

const baixarDados = () => {
  if (!userData.value) {
    return
  }

  const payload = {
    perfil: userData.value,
    preferencias: {
      armazenamentoLocal: localStorageEnabled.value,
      compartilhamentoAnalitico: analyticsSharing.value,
      bloqueioAdicional: biometricLock.value,
    },
    exportadoEm: new Date().toISOString(),
  }

  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'mente-ativa-dados.json'
  link.click()
  URL.revokeObjectURL(url)
}

const limparSessaoLocal = async () => {
  sessionStorage.removeItem('userProfile')

  try {
    await signOut(auth)
  } catch {
    // Se o Firebase não estiver disponível, ainda garantimos a limpeza local.
  }

  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-emerald-200">
    <nav class="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-20 items-center">
          <div class="flex items-center gap-3 cursor-pointer" @click="router.push('/profile')">
            <div class="bg-emerald-600 p-2.5 rounded-xl shadow-md">
              <span class="text-white text-2xl" aria-hidden="true">🛡️</span>
            </div>
            <span class="text-2xl font-bold text-slate-800 tracking-tight">Privacidade e Segurança</span>
          </div>

          <button
            @click="router.push('/profile')"
            class="px-5 py-2.5 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-800 transition-all font-bold"
          >
            Voltar
          </button>
        </div>
      </div>
    </nav>

    <main class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8">
      <section class="bg-white rounded-3xl shadow-md border border-slate-200 p-8">
        <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
          <div>
            <p class="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700 mb-3">Conta protegida</p>
            <h1 class="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">Gerencie seus dados e reduza exposição desnecessária</h1>
            <p class="text-slate-600 max-w-3xl leading-relaxed">
              Esta área reúne controles locais para privacidade, exportação de dados e encerramento de sessão.
              As preferências ficam somente no navegador.
            </p>
          </div>

          <div class="rounded-2xl bg-slate-50 border border-slate-200 p-5 min-w-[280px]">
            <p class="text-sm text-slate-500 mb-1">Status atual</p>
            <p class="text-lg font-bold text-slate-900">{{ isLogged ? 'Sessão ativa' : 'Sem sessão local' }}</p>
            <p class="text-sm text-slate-600 mt-2 break-all">{{ userData?.email || 'Nenhum usuário carregado' }}</p>
          </div>
        </div>
      </section>

      <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <article class="bg-white rounded-3xl shadow-md border border-slate-200 p-6 space-y-4">
          <div>
            <p class="text-sm font-semibold text-emerald-700 uppercase tracking-[0.18em] mb-2">Dados locais</p>
            <h2 class="text-2xl font-bold text-slate-900">Exportação e limpeza</h2>
          </div>

          <p class="text-slate-600 leading-relaxed">
            Baixe uma cópia dos dados armazenados localmente ou remova a sessão deste navegador.
          </p>

          <button
            @click="baixarDados"
            :disabled="!isLogged"
            class="w-full rounded-2xl bg-emerald-600 px-4 py-3 font-bold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Baixar meus dados
          </button>

          <button
            @click="limparSessaoLocal"
            class="w-full rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 font-bold text-rose-700 hover:bg-rose-100"
          >
            Encerrar sessão e limpar dados
          </button>
        </article>

        <article class="bg-white rounded-3xl shadow-md border border-slate-200 p-6 space-y-4">
          <div>
            <p class="text-sm font-semibold text-emerald-700 uppercase tracking-[0.18em] mb-2">Preferências</p>
            <h2 class="text-2xl font-bold text-slate-900">Controles de privacidade</h2>
          </div>

          <label class="flex items-start justify-between gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-200">
            <div>
              <p class="font-semibold text-slate-900">Armazenamento local</p>
              <p class="text-sm text-slate-600">Salvar preferências neste navegador</p>
            </div>
            <input v-model="localStorageEnabled" type="checkbox" class="mt-1 h-5 w-5 accent-emerald-600" />
          </label>

          <label class="flex items-start justify-between gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-200">
            <div>
              <p class="font-semibold text-slate-900">Compartilhamento analítico</p>
              <p class="text-sm text-slate-600">Permitir uso de dados agregados para melhoria</p>
            </div>
            <input v-model="analyticsSharing" type="checkbox" class="mt-1 h-5 w-5 accent-emerald-600" />
          </label>

          <label class="flex items-start justify-between gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-200">
            <div>
              <p class="font-semibold text-slate-900">Bloqueio adicional</p>
              <p class="text-sm text-slate-600">Exigir proteção extra no dispositivo</p>
            </div>
            <input v-model="biometricLock" type="checkbox" class="mt-1 h-5 w-5 accent-emerald-600" />
          </label>
        </article>

        <article class="bg-white rounded-3xl shadow-md border border-slate-200 p-6 space-y-4">
          <div>
            <p class="text-sm font-semibold text-emerald-700 uppercase tracking-[0.18em] mb-2">Boas práticas</p>
            <h2 class="text-2xl font-bold text-slate-900">Segurança recomendada</h2>
          </div>

          <ul class="space-y-3 text-slate-600 leading-relaxed">
            <li class="p-4 rounded-2xl bg-slate-50 border border-slate-200">Use uma senha forte e exclusiva para o acesso ao sistema.</li>
            <li class="p-4 rounded-2xl bg-slate-50 border border-slate-200">Evite manter a sessão aberta em computadores compartilhados.</li>
            <li class="p-4 rounded-2xl bg-slate-50 border border-slate-200">Revise periodicamente os dados salvos no navegador.</li>
            <li class="p-4 rounded-2xl bg-slate-50 border border-slate-200">Saia da conta ao finalizar o atendimento.</li>
          </ul>
        </article>
      </section>
    </main>
  </div>
</template>
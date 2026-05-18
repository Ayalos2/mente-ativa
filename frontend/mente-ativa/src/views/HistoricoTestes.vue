<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import DiagnosticHistoryPanel from '../components/diagnostics/DiagnosticHistoryPanel.vue'
import { carregarHistoricoTestes, formatarResultadoTeste } from '../services/testResults'
import { getCurrentUserProfile } from '../services/sessionUser'
import { downloadJson } from '../utils/downloadJson'

const router = useRouter()
const loading = ref(true)
const registros = ref([])
const carregando = ref(false)
const erro = ref('')

const abrirTestes = () => router.push('/testes')
const abrirTesteMemoria = () => router.push('/testes/memoria-curto-prazo')
const abrirTesteFluencia = () => router.push('/testes/fluencia-semantica')
const abrirTesteAtencao = () => router.push('/testes/atencao-alternada')

const baixarRegistro = (registro) => {
  downloadJson(`mente-ativa-${registro.testType || registro.testId}.json`, registro.exportPayload || registro)
}

const carregar = async () => {
  carregando.value = true
  erro.value = ''

  try {
    const profile = getCurrentUserProfile()
    if (!profile) {
      router.push('/login')
      return
    }

    const resposta = await carregarHistoricoTestes({ userProfile: profile, limitCount: 100 })
    registros.value = (resposta || []).map((r) => formatarResultadoTeste(r))
  } catch (e) {
    console.error('Erro ao carregar historico:', e)
    erro.value = 'Não foi possível carregar o histórico de testes.'
    registros.value = []
  } finally {
    carregando.value = false
    loading.value = false
  }
}

onMounted(() => carregar())
</script>

<template>
  <div class="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-emerald-200">
    <nav class="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-20 items-center">
          <div class="flex items-center gap-3 cursor-pointer" @click="router.push('/')">
            <div class="bg-emerald-600 p-2.5 rounded-xl shadow-md">
              <span class="text-white text-2xl" aria-hidden="true">🧠</span>
            </div>
            <span class="text-2xl font-bold text-slate-800 tracking-tight">Mente Ativa</span>
          </div>
          <div />
        </div>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="bg-white rounded-2xl shadow-md p-8 border border-slate-200">
        <h1 class="text-2xl font-bold text-slate-900 mb-2">Histórico de Testes</h1>
        <p class="text-slate-600 mb-6">Lista completa dos testes realizados por você.</p>

        <div v-if="carregando" class="flex items-center justify-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-300">
          <div class="animate-spin rounded-full h-10 w-10 border-4 border-slate-200 border-t-emerald-600"></div>
        </div>

        <div v-else-if="erro" class="flex flex-col items-center justify-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-300 text-center">
          <span class="text-4xl mb-4">⚠️</span>
          <p class="text-slate-600 text-lg font-medium mb-2">{{ erro }}</p>
          <button @click="carregar" class="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2.5 rounded-lg font-bold">Tentar novamente</button>
        </div>

        <DiagnosticHistoryPanel
          v-else
          :records="registros"
          @download-json="baixarRegistro"
          @rerun="(registro) => router.push(registro.testType === 'n-back-2' ? '/testes/memoria-curto-prazo' : registro.testType === 'fluencia-semantica' ? '/testes/fluencia-semantica' : '/testes/atencao-alternada')"
        />

        <div v-if="!carregando && !erro && !registros.length" class="flex flex-col items-center justify-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-300 mt-6">
          <span class="text-4xl mb-4">📋</span>
          <p class="text-slate-600 text-lg font-medium mb-2">Nenhum teste realizado ainda</p>
          <p class="text-slate-500 text-sm mb-6">Comece realizando seu primeiro teste cognitivo</p>
          <div class="flex flex-col sm:flex-row gap-3">
            <button @click="abrirTestes" class="bg-slate-900 hover:bg-slate-800 text-white px-6 py-2.5 rounded-lg font-bold">Abrir painel de testes</button>
            <button @click="abrirTesteMemoria" class="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2.5 rounded-lg font-bold">N-Back</button>
            <button @click="abrirTesteFluencia" class="bg-amber-600 hover:bg-amber-700 text-white px-6 py-2.5 rounded-lg font-bold">Fluência</button>
            <button @click="abrirTesteAtencao" class="bg-violet-600 hover:bg-violet-700 text-white px-6 py-2.5 rounded-lg font-bold">Atenção B</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
@keyframes spin { to { transform: rotate(360deg); } }
.animate-spin { animation: spin 1s linear infinite; }
</style>

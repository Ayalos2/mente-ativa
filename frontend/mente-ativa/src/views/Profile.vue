<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { signOut } from 'firebase/auth'
import { auth } from '../config/firebase'
import DiagnosticHistoryPanel from '../components/diagnostics/DiagnosticHistoryPanel.vue'
import { carregarHistoricoTestes, formatarResultadoTeste } from '../services/testResults'
import { getCurrentUserProfile } from '../services/sessionUser'
import { downloadJson } from '../utils/downloadJson'
import { carregarPacientesDoMedico, carregarTestesDoPaciente, vincularPacientePorEmail } from '../services/doctorLinks'

const router = useRouter()
const userData = ref(null)
const loading = ref(true)
const historicoTestes = ref([])
const carregandoHistorico = ref(false)
const erroHistorico = ref('')
const cargoEhEspecialista = computed(() => userData.value?.cargo === 'especialista')
const emailPacienteVinculo = ref('')
const carregandoVinculos = ref(false)
const erroVinculos = ref('')
const pacientesVinculados = ref([])
const pacienteSelecionado = ref(null)
const testesPacienteSelecionado = ref([])
const carregandoTestesPaciente = ref(false)
const erroTestesPaciente = ref('')

const totalTestes = computed(() => historicoTestes.value.length)
const mediaPrecisao = computed(() => {
  if (!historicoTestes.value.length) {
    return 0
  }

  const soma = historicoTestes.value.reduce((acumulado, teste) => {
    const percentual = teste.accuracyPercent || Math.round(((teste.totalCorrect || 0) / Math.max(teste.totalClicks || 1, 1)) * 100)
    return acumulado + percentual
  }, 0)
  return Math.round(soma / historicoTestes.value.length)
})
const ultimoTeste = computed(() => historicoTestes.value[0] || null)

const formatarDataHora = (valor) => {
  if (!valor) {
    return 'Sem data'
  }

  const data = new Date(valor)
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(data)
}

const abrirTestes = () => {
  router.push('/testes')
}

const abrirTesteMemoria = () => {
  router.push('/testes/memoria-curto-prazo')
}

const abrirTesteFluencia = () => {
  router.push('/testes/fluencia-semantica')
}

const abrirTesteAtencao = () => {
  router.push('/testes/atencao-alternada')
}

const formatarResumoTeste = (teste) => {
  if (!teste) {
    return 'Sem testes'
  }

  const resumo = teste.summary || {}
  const precisa = resumo.accuracyPercent ?? resumo.totalCorrect ?? resumo.correctResponses ?? 0
  const tempo = resumo.averageLatencyMs ?? resumo.completionTimeMs ?? resumo.averageResponseMs ?? 0

  return `${precisa}% | ${tempo} ms`
}

const selecionarPaciente = async (paciente) => {
  pacienteSelecionado.value = paciente
  carregandoTestesPaciente.value = true
  erroTestesPaciente.value = ''

  try {
    const resposta = await carregarTestesDoPaciente(paciente.patientUid)
    testesPacienteSelecionado.value = resposta.data.tests || []
  } catch (error) {
    console.error('Erro ao carregar testes do paciente:', error)
    erroTestesPaciente.value = error?.response?.data?.detail || 'Nao foi possivel carregar os testes do paciente.'
    testesPacienteSelecionado.value = []
  } finally {
    carregandoTestesPaciente.value = false
  }
}

const carregarVinculos = async () => {
  if (!cargoEhEspecialista.value) {
    return
  }

  carregandoVinculos.value = true
  erroVinculos.value = ''

  try {
    const resposta = await carregarPacientesDoMedico()
    pacientesVinculados.value = resposta.data.patients || []

    if (pacientesVinculados.value.length) {
      const pacienteAtual = pacientesVinculados.value.find((paciente) => pacienteSelecionado.value?.patientUid === paciente.patientUid) || pacientesVinculados.value[0]
      await selecionarPaciente(pacienteAtual)
    } else {
      pacienteSelecionado.value = null
      testesPacienteSelecionado.value = []
    }
  } catch (error) {
    console.error('Erro ao carregar pacientes vinculados:', error)
    erroVinculos.value = error?.response?.data?.detail || 'Nao foi possivel carregar os pacientes vinculados.'
  } finally {
    carregandoVinculos.value = false
  }
}

const vincularPaciente = async () => {
  erroVinculos.value = ''

  if (!emailPacienteVinculo.value.trim()) {
    erroVinculos.value = 'Informe o e-mail do paciente.'
    return
  }

  carregandoVinculos.value = true

  try {
    await vincularPacientePorEmail(emailPacienteVinculo.value.trim())
    emailPacienteVinculo.value = ''
    await carregarVinculos()
  } catch (error) {
    console.error('Erro ao vincular paciente:', error)
    erroVinculos.value = error?.response?.data?.detail || 'Nao foi possivel vincular o paciente.'
  } finally {
    carregandoVinculos.value = false
  }
}

const carregarHistorico = async () => {
  carregandoHistorico.value = true
  erroHistorico.value = ''

  try {
    const registros = await carregarHistoricoTestes({ userProfile: getCurrentUserProfile(), limitCount: 20 })
    historicoTestes.value = registros.map((registro) => formatarResultadoTeste(registro))
  } catch (error) {
    console.error('Erro ao carregar historico de testes:', error)
    erroHistorico.value = 'Nao foi possivel carregar o historico dos testes.'
  } finally {
    carregandoHistorico.value = false
  }
}

onMounted(() => {
  // Obtém dados do usuário armazenados no sessionStorage
  const storedUser = sessionStorage.getItem('userProfile')
  
  if (storedUser) {
    userData.value = JSON.parse(storedUser)
    carregarHistorico()

    if (JSON.parse(storedUser)?.cargo === 'especialista') {
      carregarVinculos()
    }
  } else {
    // Se não houver dados, redireciona para login
    router.push('/login')
  }
  
  loading.value = false
})

const handleLogout = async () => {
  try {
    await signOut(auth)
    sessionStorage.removeItem('userProfile')
    router.push('/login')
  } catch (error) {
    console.error('Erro ao fazer logout:', error)
    alert('Erro ao fazer logout')
  }
}

const abrirPrivacidadeSeguranca = () => {
  router.push('/profile/privacy-security')
}

const baixarRegistro = (registro) => {
  downloadJson(`mente-ativa-${registro.testType || registro.testId}.json`, registro.exportPayload || registro)
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-emerald-200">
    
    <!-- Navbar -->
    <nav class="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-20 items-center">
          
          <div class="flex items-center gap-3 cursor-pointer" @click="router.push('/')">
            <div class="bg-emerald-600 p-2.5 rounded-xl shadow-md">
              <span class="text-white text-2xl" aria-hidden="true">🧠</span>
            </div>
            <span class="text-2xl font-bold text-slate-800 tracking-tight">Mente Ativa</span>
          </div>

          <div class="flex items-center gap-4">
            <button 
              @click="handleLogout"
              class="px-6 py-2.5 rounded-full bg-slate-100 hover:bg-red-100 text-slate-800 hover:text-red-700 transition-all font-bold focus:ring-2 focus:ring-slate-400 outline-none"
            >
              Sair
            </button>
          </div>

        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      
      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-24">
        <div class="animate-spin rounded-full h-12 w-12 border-4 border-slate-200 border-t-emerald-600"></div>
      </div>

      <!-- Profile Content -->
      <div v-else-if="userData" class="space-y-8">
        
        <!-- Profile Header -->
        <div class="bg-white rounded-2xl shadow-md p-8 border border-slate-200">
          <div class="flex items-start justify-between">
            <div class="flex items-center gap-6">
              <div class="w-24 h-24 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-2xl flex items-center justify-center shadow-lg">
                <span class="text-4xl">👤</span>
              </div>
              <div>
                <h1 class="text-3xl font-bold text-slate-900 mb-2">{{ userData.nome || userData.email }}</h1>
                <p class="text-slate-600 text-lg mb-3">{{ userData.email }}</p>
                <div class="flex items-center gap-2">
                  <div class="w-3 h-3 bg-emerald-500 rounded-full"></div>
                  <span class="text-sm font-medium text-emerald-700">
                    Conectado via {{ userData.provedor === 'google' ? 'Google' : 'Email/Senha' }}
                  </span>
                </div>
              </div>
            </div>
            <div class="flex flex-col sm:flex-row gap-3">
              <button 
                @click="abrirTestes"
                class="bg-slate-900 hover:bg-slate-800 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg shadow-slate-200 active:scale-95 focus:outline-none focus:ring-4 focus:ring-slate-300"
              >
                Abrir painel de testes
              </button>
              <button 
                @click="abrirTesteMemoria"
                class="bg-emerald-600 hover:bg-emerald-700 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg shadow-emerald-200 active:scale-95 focus:outline-none focus:ring-4 focus:ring-emerald-300"
              >
                N-Back
              </button>
              <button 
                @click="abrirTesteFluencia"
                class="bg-amber-600 hover:bg-amber-700 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg shadow-amber-200 active:scale-95 focus:outline-none focus:ring-4 focus:ring-amber-300"
              >
                Fluência
              </button>
              <button 
                @click="abrirTesteAtencao"
                class="bg-violet-600 hover:bg-violet-700 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg shadow-violet-200 active:scale-95 focus:outline-none focus:ring-4 focus:ring-violet-300"
              >
                Atenção B
              </button>
            </div>
          </div>
        </div>

        <!-- Stats Grid -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          <div class="bg-white rounded-2xl shadow-md p-6 border border-slate-200">
            <div class="flex items-center gap-4">
              <div class="w-16 h-16 bg-blue-50 rounded-xl flex items-center justify-center text-2xl">
                📊
              </div>
              <div>
                <p class="text-sm text-slate-600 font-medium mb-1">Testes Realizados</p>
                <p class="text-3xl font-bold text-slate-900">{{ totalTestes }}</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-2xl shadow-md p-6 border border-slate-200">
            <div class="flex items-center gap-4">
              <div class="w-16 h-16 bg-purple-50 rounded-xl flex items-center justify-center text-2xl">
                📈
              </div>
              <div>
                <p class="text-sm text-slate-600 font-medium mb-1">Pontuação Média</p>
                <p class="text-3xl font-bold text-slate-900">{{ totalTestes ? `${mediaPrecisao}%` : '-' }}</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-2xl shadow-md p-6 border border-slate-200">
            <div class="flex items-center gap-4">
              <div class="w-16 h-16 bg-emerald-50 rounded-xl flex items-center justify-center text-2xl">
                ⏱️
              </div>
              <div>
                <p class="text-sm text-slate-600 font-medium mb-1">Última Atualização</p>
                <p class="text-lg font-bold text-slate-900">{{ ultimoTeste ? formatarDataHora(ultimoTeste.createdAtMs) : 'Hoje' }}</p>
              </div>
            </div>
          </div>

        </div>

        <!-- Recent Tests -->
        <div v-if="cargoEhEspecialista" class="bg-white rounded-2xl shadow-md p-8 border border-slate-200">
          <div class="flex items-start justify-between gap-4 mb-6">
            <div>
              <h2 class="text-2xl font-bold text-slate-900">Vínculo médico-paciente</h2>
              <p class="text-slate-600 mt-2">Vincule pacientes pelo e-mail e acesse os testes deles em uma lista própria.</p>
            </div>
            <div class="text-sm font-semibold text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-full px-4 py-2">
              Área restrita para especialistas
            </div>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="lg:col-span-1 space-y-4">
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">E-mail do paciente</label>
                <input
                  v-model="emailPacienteVinculo"
                  type="email"
                  placeholder="paciente@email.com"
                  class="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-emerald-500 focus:border-emerald-500 text-slate-900"
                />
              </div>

              <button
                @click="vincularPaciente"
                :disabled="carregandoVinculos"
                class="w-full bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-3 rounded-xl font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ carregandoVinculos ? 'Vinculando...' : 'Vincular paciente' }}
              </button>

              <p v-if="erroVinculos" class="text-sm font-medium text-red-700 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
                {{ erroVinculos }}
              </p>

              <p class="text-xs text-slate-500">
                O paciente precisa estar cadastrado no sistema com o mesmo e-mail informado.
              </p>
            </div>

            <div class="lg:col-span-2">
              <div v-if="carregandoVinculos" class="flex items-center justify-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-300">
                <div class="animate-spin rounded-full h-8 w-8 border-4 border-slate-200 border-t-emerald-600"></div>
              </div>

              <div v-else-if="!pacientesVinculados.length" class="flex flex-col items-center justify-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-300 text-center">
                <span class="text-4xl mb-3">👥</span>
                <p class="text-lg font-bold text-slate-900">Nenhum paciente vinculado</p>
                <p class="text-sm text-slate-600 mt-1">Use o e-mail do paciente para criar o vínculo e liberar os testes.</p>
              </div>

              <div v-else class="space-y-3 max-h-[26rem] overflow-y-auto pr-1">
                <button
                  v-for="paciente in pacientesVinculados"
                  :key="paciente.patientUid"
                  @click="selecionarPaciente(paciente)"
                  class="w-full text-left rounded-2xl border p-4 transition-all"
                  :class="pacienteSelecionado?.patientUid === paciente.patientUid ? 'border-emerald-300 bg-emerald-50' : 'border-slate-200 bg-white hover:bg-slate-50'"
                >
                  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div>
                      <p class="font-bold text-slate-900">{{ paciente.patientName }}</p>
                      <p class="text-sm text-slate-600">{{ paciente.patientEmail }}</p>
                    </div>
                    <div class="text-sm text-slate-500 sm:text-right">
                      <p>{{ paciente.testsCount || 0 }} teste(s)</p>
                      <p>Vinculado em {{ formatarDataHora(paciente.linkedAtMs) }}</p>
                    </div>
                  </div>
                  <p class="mt-3 text-sm text-slate-700">
                    Último teste: {{ paciente.latestTest ? `${paciente.latestTest.testName} · ${formatarDataHora(paciente.latestTest.createdAtMs)}` : 'Nenhum teste registrado' }}
                  </p>
                </button>
              </div>
            </div>
          </div>

          <div v-if="pacienteSelecionado" class="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-6">
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
              <div>
                <h3 class="text-xl font-bold text-slate-900">{{ pacienteSelecionado.patientName }}</h3>
                <p class="text-sm text-slate-600">{{ pacienteSelecionado.patientEmail }}</p>
              </div>
              <div class="text-sm font-semibold text-slate-700 bg-white border border-slate-200 rounded-full px-4 py-2">
                {{ testesPacienteSelecionado.length }} teste(s) acessível(is)
              </div>
            </div>

            <div v-if="carregandoTestesPaciente" class="flex items-center justify-center py-8">
              <div class="animate-spin rounded-full h-8 w-8 border-4 border-slate-200 border-t-emerald-600"></div>
            </div>

            <p v-else-if="erroTestesPaciente" class="text-sm font-medium text-red-700 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
              {{ erroTestesPaciente }}
            </p>

            <div v-else-if="testesPacienteSelecionado.length" class="grid gap-4 md:grid-cols-2">
              <article
                v-for="teste in testesPacienteSelecionado"
                :key="teste.id"
                class="rounded-2xl border border-white bg-white p-4 shadow-sm"
              >
                <div class="flex items-start justify-between gap-4">
                  <div>
                    <p class="font-bold text-slate-900">{{ teste.testName }}</p>
                    <p class="text-xs text-slate-500">{{ formatarDataHora(teste.createdAtMs) }}</p>
                  </div>
                  <span class="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">
                    {{ teste.testTypeLabel || teste.testType || teste.testId }}
                  </span>
                </div>

                <p class="mt-3 text-sm text-slate-700">Resumo: {{ formatarResumoTeste(teste) }}</p>
                <div class="mt-4 flex flex-wrap gap-2 text-xs text-slate-600">
                  <span class="rounded-full bg-slate-100 px-3 py-1">Clicks: {{ teste.totalClicks || 0 }}</span>
                  <span class="rounded-full bg-slate-100 px-3 py-1">Erros: {{ teste.errorCount || 0 }}</span>
                  <span class="rounded-full bg-slate-100 px-3 py-1">Acertos: {{ teste.totalCorrect || teste.correctResponses || 0 }}</span>
                </div>
              </article>
            </div>

            <div v-else class="text-sm text-slate-600 bg-white border border-dashed border-slate-300 rounded-2xl p-5">
              Este paciente ainda não possui testes registrados.
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-md p-8 border border-slate-200">
          <h2 class="text-2xl font-bold text-slate-900 mb-6">Histórico de Testes</h2>
          
          <div v-if="carregandoHistorico" class="flex items-center justify-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-300">
            <div class="animate-spin rounded-full h-10 w-10 border-4 border-slate-200 border-t-emerald-600"></div>
          </div>

          <div v-else-if="erroHistorico" class="flex flex-col items-center justify-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-300 text-center">
            <span class="text-4xl mb-4">⚠️</span>
            <p class="text-slate-600 text-lg font-medium mb-2">{{ erroHistorico }}</p>
            <button 
              @click="carregarHistorico"
              class="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2.5 rounded-lg font-bold transition-all focus:outline-none focus:ring-4 focus:ring-emerald-300"
            >
              Tentar novamente
            </button>
          </div>

          <DiagnosticHistoryPanel
            v-else-if="historicoTestes.length"
            :records="historicoTestes"
            @download-json="baixarRegistro"
            @rerun="(registro) => router.push(registro.testType === 'n-back-2' ? '/testes/memoria-curto-prazo' : registro.testType === 'fluencia-semantica' ? '/testes/fluencia-semantica' : '/testes/atencao-alternada')"
          />

          <div v-else class="flex flex-col items-center justify-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-300">
            <span class="text-4xl mb-4">📋</span>
            <p class="text-slate-600 text-lg font-medium mb-2">Nenhum teste realizado ainda</p>
            <p class="text-slate-500 text-sm mb-6">Comece realizando seu primeiro teste cognitivo</p>
            <div class="flex flex-col sm:flex-row gap-3">
              <button 
                @click="abrirTestes"
                class="bg-slate-900 hover:bg-slate-800 text-white px-6 py-2.5 rounded-lg font-bold transition-all focus:outline-none focus:ring-4 focus:ring-slate-300"
              >
                Abrir painel de testes
              </button>
              <button 
                @click="abrirTesteMemoria"
                class="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2.5 rounded-lg font-bold transition-all focus:outline-none focus:ring-4 focus:ring-emerald-300"
              >
                N-Back
              </button>
              <button 
                @click="abrirTesteFluencia"
                class="bg-amber-600 hover:bg-amber-700 text-white px-6 py-2.5 rounded-lg font-bold transition-all focus:outline-none focus:ring-4 focus:ring-amber-300"
              >
                Fluência
              </button>
              <button 
                @click="abrirTesteAtencao"
                class="bg-violet-600 hover:bg-violet-700 text-white px-6 py-2.5 rounded-lg font-bold transition-all focus:outline-none focus:ring-4 focus:ring-violet-300"
              >
                Atenção B
              </button>
            </div>
          </div>
        </div>

        <!-- Settings Section -->
        <div class="bg-white rounded-2xl shadow-md p-8 border border-slate-200">
          <h2 class="text-2xl font-bold text-slate-900 mb-6">Configurações da Conta</h2>
          
          <div class="space-y-4">
            <div class="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200 hover:bg-slate-100 transition-colors cursor-pointer" @click="router.push('/profile/edit')">
              <div>
                <p class="font-medium text-slate-900">Editar Perfil</p>
                <p class="text-sm text-slate-600">Atualize suas informações pessoais</p>
              </div>
              <span class="text-xl">→</span>
            </div>

            <div class="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200 hover:bg-slate-100 transition-colors cursor-pointer">
              <div>
                <p class="font-medium text-slate-900">Notificações</p>
                <p class="text-sm text-slate-600">Gerenciar preferências de notificações</p>
              </div>
              <span class="text-xl">→</span>
            </div>

            <div
              class="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200 hover:bg-slate-100 transition-colors cursor-pointer"
              @click="abrirPrivacidadeSeguranca"
            >
              <div>
                <p class="font-medium text-slate-900">Privacidade e Segurança</p>
                <p class="text-sm text-slate-600">Controle sua privacidade de dados</p>
              </div>
              <span class="text-xl">→</span>
            </div>
          </div>
        </div>

      </div>

      <!-- Not Logged In State -->
      <div v-else class="text-center py-24">
        <span class="text-5xl mb-6 block">🔒</span>
        <h2 class="text-2xl font-bold text-slate-900 mb-3">Acesso Restrito</h2>
        <p class="text-slate-600 mb-8">Você precisa estar conectado para acessar seu perfil</p>
        <button 
          @click="router.push('/login')"
          class="bg-emerald-600 hover:bg-emerald-700 text-white px-8 py-3 rounded-xl font-bold transition-all focus:outline-none focus:ring-4 focus:ring-emerald-300"
        >
          Ir para Login
        </button>
      </div>

    </main>

  </div>
</template>

<style scoped>
/* Animação de loading spinner */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>

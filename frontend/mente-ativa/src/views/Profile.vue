<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { signOut } from 'firebase/auth'
import { doc, getDoc } from 'firebase/firestore'
import { auth, db } from '../config/firebase'
import { onAuthStateChanged } from 'firebase/auth'
import DiagnosticHistoryPanel from '../components/diagnostics/DiagnosticHistoryPanel.vue'
import { carregarHistoricoTestes, formatarResultadoTeste } from '../services/testResults'
import { getCurrentUserProfile } from '../services/sessionUser'
import { downloadJson } from '../utils/downloadJson'
import {
  carregarPacientesDoMedico,
  carregarTestesDoPaciente,
  vincularPacientePorEmail,
  carregarMeusMedicos,
  carregarMeuResumoSaude,
  gerarResumoPaciente,
  salvarDiagnosticoPaciente,
  carregarDiagnosticoPaciente,
  publicarResumoParaPaciente,
} from '../services/doctorLinks'

const router = useRouter()
const userData = ref(null)
const loading = ref(true)
const historicoTestes = ref([])
const carregandoHistorico = ref(false)
const erroHistorico = ref('')
const cargoEhEspecialista = computed(() => userData.value?.cargo === 'especialista')
const cargoEhPaciente = computed(() => userData.value?.cargo === 'paciente' || !userData.value?.cargo)
const meusMedicos = ref([])
const carregandoMeusMedicos = ref(false)
const erroMeusMedicos = ref('')

// ====== Paciente: Resumo de Saúde ======
const resumoPaciente = ref(null)
const carregandoResumoPacienteProprio = ref(false)
const erroResumoPacienteProprio = ref('')
const resumoDisponivel = ref(false)
const diagnosticoMedicoPaciente = ref(null)
const carregandoDiagnosticoPaciente = ref(false)
const erroDiagnosticoPaciente = ref('')

// ====== Médico: Vínculos ======
const emailPacienteVinculo = ref('')
const carregandoVinculos = ref(false)
const erroVinculos = ref('')
const pacientesVinculados = ref([])
const filtroPacientes = ref('')
const pacienteSelecionado = ref(null)
const testesPacienteSelecionado = ref([])
const carregandoTestesPaciente = ref(false)
const erroTestesPaciente = ref('')

let selecaoPacienteToken = 0

// ====== Médico: Geração de Resumo LLM ======
const gerandoResumoLLM = ref(false)
const erroGerarResumoLLM = ref('')
const resumoLLMResultado = ref(null)
const resumoLLMDadosBrutos = ref(null)

// ====== Médico: Diagnóstico ======
const textoDiagnostico = ref('')
const salvandoDiagnostico = ref(false)
const erroSalvarDiagnostico = ref('')
const diagnosticoSalvo = ref(null)
const carregandoDiagnostico = ref(false)
const erroCarregarDiagnostico = ref('')

// ====== Médico: Publicar ======
const publicandoResumo = ref(false)
const erroPublicarResumo = ref('')
const resumoPublicado = ref(false)
const sumarioPublicacao = ref(null)

// ====== Computed ======
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

const pacientesFiltrados = computed(() => {
  const termo = filtroPacientes.value.trim().toLowerCase()

  if (!termo) {
    return pacientesVinculados.value
  }

  return pacientesVinculados.value.filter((paciente) => {
    const nome = (paciente.patientName || '').toLowerCase()
    const email = (paciente.patientEmail || '').toLowerCase()
    return nome.includes(termo) || email.includes(termo)
  })
})

// ====== Utilitários ======
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

const obterStatusOtimo = (paciente) => {
  const resumo = paciente?.latestTest?.summary || paciente?.latestTest || {}
  const accuracy = Number(resumo.accuracyPercent ?? resumo.totalCorrect ?? resumo.correctResponses ?? 0)

  if (!paciente?.testsCount) {
    return 'Sem testes'
  }

  return accuracy >= 80 ? 'Ótimo' : 'Não'
}

// ====== Médico: Selecionar paciente ======
const selecionarPaciente = async (paciente) => {
  const tokenAtual = ++selecaoPacienteToken
  pacienteSelecionado.value = paciente
  carregandoTestesPaciente.value = true
  erroTestesPaciente.value = ''
  resumoLLMResultado.value = null
  resumoLLMDadosBrutos.value = null
  erroGerarResumoLLM.value = ''
  textoDiagnostico.value = ''
  diagnosticoSalvo.value = null
  erroSalvarDiagnostico.value = ''
  erroCarregarDiagnostico.value = ''
  resumoPublicado.value = false
  sumarioPublicacao.value = null

  try {
    const testesResposta = await carregarTestesDoPaciente(paciente.patientUid)

    if (tokenAtual !== selecaoPacienteToken) {
      return
    }

    if (testesResposta.status === 200) {
      testesPacienteSelecionado.value = (testesResposta.data.tests || []).map((t) => formatarResultadoTeste(t))
    }
  } catch (error) {
    console.error('Erro ao carregar testes do paciente:', error)
    erroTestesPaciente.value = error?.response?.data?.detail || 'Nao foi possivel carregar os testes do paciente.'
    testesPacienteSelecionado.value = []
  } finally {
    if (tokenAtual === selecaoPacienteToken) {
      carregandoTestesPaciente.value = false
    }
  }
}

const limparPacienteSelecionado = () => {
  selecaoPacienteToken += 1
  pacienteSelecionado.value = null
  testesPacienteSelecionado.value = []
  resumoLLMResultado.value = null
  resumoLLMDadosBrutos.value = null
  textoDiagnostico.value = ''
  diagnosticoSalvo.value = null
  erroTestesPaciente.value = ''
  erroGerarResumoLLM.value = ''
  erroSalvarDiagnostico.value = ''
  erroCarregarDiagnostico.value = ''
  resumoPublicado.value = false
  sumarioPublicacao.value = null
}

// ====== Médico: Carregar vínculos ======
const carregarVinculos = async () => {
  if (!cargoEhEspecialista.value) {
    return
  }

  carregandoVinculos.value = true
  erroVinculos.value = ''

  try {
    const resposta = await carregarPacientesDoMedico()
    pacientesVinculados.value = resposta.data.patients || []

    if (pacientesFiltrados.value.length) {
      const pacienteAtual = pacientesFiltrados.value.find((paciente) => pacienteSelecionado.value?.patientUid === paciente.patientUid) || pacientesFiltrados.value[0]
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

// ====== Paciente: Carregar médicos ======
const carregarMeusMedicosDoServidor = async () => {
  if (!cargoEhPaciente.value) {
    return
  }

  carregandoMeusMedicos.value = true
  erroMeusMedicos.value = ''

  try {
    const resposta = await carregarMeusMedicos()
    meusMedicos.value = resposta.data.doctors || []
  } catch (error) {
    console.error('Erro ao carregar meus medicos:', error)
    erroMeusMedicos.value = error?.response?.data?.detail || 'Nao foi possivel carregar os medicos vinculados.'
    meusMedicos.value = []
  } finally {
    carregandoMeusMedicos.value = false
  }
}

// ====== Paciente: Carregar resumo e diagnóstico ======
const carregarMeuResumoSaudeDoServidor = async () => {
  if (!cargoEhPaciente.value) return

  carregandoResumoPacienteProprio.value = true
  erroResumoPacienteProprio.value = ''
  resumoPaciente.value = null
  resumoDisponivel.value = false

  try {
    const resposta = await carregarMeuResumoSaude()
    if (resposta.data.hasSummary && resposta.data.summary) {
      // Só mostra se o médico disponibilizou (availableToPatient)
      const disponivel = resposta.data.availableToPatient === true
      if (disponivel) {
        resumoPaciente.value = resposta.data
        resumoDisponivel.value = true
      }
    }
  } catch (error) {
    console.error('Erro ao carregar resumo de saude:', error)
    erroResumoPacienteProprio.value = error?.response?.data?.detail || ''
  } finally {
    carregandoResumoPacienteProprio.value = false
  }
}

// ====== Médico: Gerar resumo LLM ======
const gerarResumoLLMMedico = async () => {
  if (!pacienteSelecionado.value) return

  gerandoResumoLLM.value = true
  erroGerarResumoLLM.value = ''
  resumoLLMResultado.value = null
  resumoLLMDadosBrutos.value = null

  try {
    const resposta = await gerarResumoPaciente(pacienteSelecionado.value.patientUid)
    resumoLLMResultado.value = resposta.data
    resumoLLMDadosBrutos.value = resposta.data.summary
  } catch (error) {
    console.error('Erro ao gerar resumo LLM:', error)
    erroGerarResumoLLM.value = error?.response?.data?.detail || 'Nao foi possivel gerar o resumo LLM.'
  } finally {
    gerandoResumoLLM.value = false
  }
}

// ====== Médico: Salvar diagnóstico ======
const salvarDiagnosticoMedico = async () => {
  if (!pacienteSelecionado.value) return
  if (!textoDiagnostico.value.trim()) {
    erroSalvarDiagnostico.value = 'O diagnostico nao pode estar vazio.'
    return
  }

  salvandoDiagnostico.value = true
  erroSalvarDiagnostico.value = ''

  try {
    const resposta = await salvarDiagnosticoPaciente(pacienteSelecionado.value.patientUid, textoDiagnostico.value.trim())
    diagnosticoSalvo.value = resposta.data
  } catch (error) {
    console.error('Erro ao salvar diagnostico:', error)
    erroSalvarDiagnostico.value = error?.response?.data?.detail || 'Nao foi possivel salvar o diagnostico.'
  } finally {
    salvandoDiagnostico.value = false
  }
}

// ====== Médico: Publicar resumo para paciente ======
const publicarResumoMedico = async () => {
  if (!pacienteSelecionado.value) return

  publicandoResumo.value = true
  erroPublicarResumo.value = ''

  try {
    const resposta = await publicarResumoParaPaciente(pacienteSelecionado.value.patientUid)
    resumoPublicado.value = true
    sumarioPublicacao.value = resposta.data
  } catch (error) {
    console.error('Erro ao publicar resumo:', error)
    erroPublicarResumo.value = error?.response?.data?.detail || 'Nao foi possivel disponibilizar o resumo para o paciente.'
  } finally {
    publicandoResumo.value = false
  }
}

// ====== Médico: Recarregar testes ======
const recarregarHistoricoPacienteSelecionado = async () => {
  if (!pacienteSelecionado.value) {
    return
  }

  await selecionarPaciente(pacienteSelecionado.value)
}

// ====== Vinculação ======
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

// ====== Histórico próprio ======
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

const baixarHistoricoPacienteSelecionado = (registro) => {
  if (!pacienteSelecionado.value) {
    return
  }

  downloadJson(
    `mente-ativa-${pacienteSelecionado.value.patientUid}-${registro.testType || registro.testId}.json`,
    registro.exportPayload || registro
  )
}

const baixarRegistro = (registro) => {
  downloadJson(`mente-ativa-${registro.testType || registro.testId}.json`, registro.exportPayload || registro)
}

// ====== Lifecycle ======
onMounted(() => {
  const carregarPerfilEConteudo = async () => {
    const storedUser = sessionStorage.getItem('userProfile')

    if (!storedUser) {
      router.push('/login')
      loading.value = false
      return
    }

    const parsedUser = JSON.parse(storedUser)

    try {
      const userUid = parsedUser?.uid
      if (userUid && (!parsedUser.cargo || parsedUser.cargo === 'paciente')) {
        const userDoc = await getDoc(doc(db, 'usuarios', userUid))
        if (userDoc.exists()) {
          const userDocData = userDoc.data() || {}
          parsedUser.cargo = userDocData.cargo || parsedUser.cargo
          parsedUser.nome = userDocData.nome || parsedUser.nome
          parsedUser.foto = userDocData.foto || parsedUser.foto
          sessionStorage.setItem('userProfile', JSON.stringify(parsedUser))
        }
      }
    } catch (error) {
      console.warn('Nao foi possivel atualizar o perfil do usuario a partir do Firestore:', error)
    }

    userData.value = parsedUser
    await carregarHistorico()

    // Garantir que o auth.currentUser esteja disponível antes de chamar endpoints protegidos
    const waitForAuthUser = () => new Promise((resolve) => {
      if (auth.currentUser) return resolve(auth.currentUser)
      const unsub = onAuthStateChanged(auth, (user) => {
        unsub()
        resolve(user)
      })
      // fallback em 5s
      setTimeout(() => resolve(auth.currentUser), 5000)
    })

    await waitForAuthUser()

    if (parsedUser?.cargo === 'especialista') {
      await carregarVinculos()
    } else {
      await carregarMeusMedicosDoServidor()
      await carregarMeuResumoSaudeDoServidor()
    }

    loading.value = false
  }

  carregarPerfilEConteudo()
})

const handleLogout = async () => {
  try {
    await signOut(auth)
    sessionStorage.removeItem('userProfile')
    sessionStorage.removeItem('firebaseIdToken')
    router.push('/login')
  } catch (error) {
    console.error('Erro ao fazer logout:', error)
    alert('Erro ao fazer logout')
  }
}

const abrirPrivacidadeSeguranca = () => {
  router.push('/profile/privacy-security')
}

const showNotifications = ref(false)

const abrirHistorico = () => {
  router.push('/profile/historico')
}

const abrirDiagnosticoPacienteView = () => {
  router.push('/profile/historico')
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

        <!-- ==================== SEÇÃO DO MÉDICO ==================== -->
        <div v-if="cargoEhEspecialista" class="bg-white rounded-2xl shadow-md p-8 border border-slate-200">
          <div class="flex items-start justify-between gap-4 mb-6">
            <div>
              <h2 class="text-2xl font-bold text-slate-900">Vínculo médico-paciente</h2>
              <p class="text-slate-600 mt-2">Vincule pacientes pelo e-mail, gere resumo LLM, digite o diagnóstico e disponibilize para o paciente.</p>
            </div>
            <div class="text-sm font-semibold text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-full px-4 py-2">
              Área restrita para especialistas
            </div>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Coluna esquerda: Busca e vínculo -->
            <div class="lg:col-span-1 space-y-4">
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Pesquisar paciente vinculado</label>
                <input
                  v-model="filtroPacientes"
                  type="text"
                  placeholder="Buscar por nome ou e-mail"
                  class="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-emerald-500 focus:border-emerald-500 text-slate-900"
                />
              </div>

              <p class="text-xs text-slate-500">
                {{ pacientesFiltrados.length }} paciente(s) encontrado(s).
              </p>

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

            <!-- Coluna direita: Lista de pacientes -->
            <div class="lg:col-span-2">
              <div v-if="carregandoVinculos" class="flex items-center justify-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-300">
                <div class="animate-spin rounded-full h-8 w-8 border-4 border-slate-200 border-t-emerald-600"></div>
              </div>

              <div v-else-if="!pacientesFiltrados.length" class="flex flex-col items-center justify-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-300 text-center">
                <span class="text-4xl mb-3">👥</span>
                <p class="text-lg font-bold text-slate-900">Nenhum paciente encontrado</p>
                <p class="text-sm text-slate-600 mt-1">Tente outro nome/e-mail ou vincule um paciente pelo e-mail acima.</p>
              </div>

              <div v-else class="space-y-3 max-h-[26rem] overflow-y-auto pr-1">
                <button
                  v-for="paciente in pacientesFiltrados"
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
                      <p>
                        Status:
                        <span :class="obterStatusOtimo(paciente) === 'Ótimo' ? 'text-emerald-700 font-bold' : 'text-slate-700 font-semibold'">
                          {{ obterStatusOtimo(paciente) }}
                        </span>
                      </p>
                    </div>
                  </div>
                </button>
              </div>

              <div class="pt-2">
                <p class="text-xs text-slate-500">Clique em um paciente para ver o histórico, gerar resumo LLM e diagnóstico.</p>
              </div>
            </div>
          </div>

          <!-- Painel do paciente selecionado (Médico) -->
          <div v-if="pacienteSelecionado" class="mt-8 space-y-6">
            <!-- Cabeçalho do paciente -->
            <div class="bg-slate-50 rounded-2xl border border-slate-200 p-5">
              <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 class="text-xl font-bold text-slate-900">{{ pacienteSelecionado.patientName }}</h3>
                  <p class="text-sm text-slate-600">{{ pacienteSelecionado.patientEmail }}</p>
                </div>
                <div class="flex flex-col sm:flex-row sm:items-center gap-3">
                  <button
                    @click="limparPacienteSelecionado"
                    class="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-sm font-semibold transition-all"
                  >
                    Fechar
                  </button>
                </div>
              </div>
            </div>

            <!-- Médico: Gerar resumo LLM -->
            <div class="bg-white rounded-2xl border border-amber-200 p-5">
              <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p class="text-xs font-black uppercase tracking-[0.25em] text-amber-700">Resumo automático LLM</p>
                  <h4 class="mt-1 text-lg font-bold text-slate-900">Gerar leitura clínica do histórico</h4>
                  <p class="text-sm text-slate-600 mt-1">O resumo será gerado com base nos testes cognitivos do paciente.</p>
                </div>
                <div class="flex flex-col items-start gap-2 sm:items-end">
                  <button
                    @click="gerarResumoLLMMedico"
                    :disabled="gerandoResumoLLM || testesPacienteSelecionado.length === 0"
                    class="rounded-full bg-amber-600 px-4 py-2 text-xs font-bold text-white hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {{ gerandoResumoLLM ? 'Gerando...' : 'Gerar resumo LLM' }}
                  </button>
                  <p v-if="testesPacienteSelecionado.length === 0 && !carregandoTestesPaciente" class="text-xs text-amber-600">
                    Precisa de pelo menos um teste.
                  </p>
                </div>
              </div>

              <!-- Loading -->
              <div v-if="gerandoResumoLLM" class="mt-4 flex items-center gap-3 rounded-xl bg-amber-50/80 px-4 py-3 text-sm text-slate-600">
                <div class="h-4 w-4 animate-spin rounded-full border-2 border-slate-200 border-t-amber-600"></div>
                Gerando resumo com base nos dados coletados do paciente...
              </div>

              <!-- Erro -->
              <p v-if="erroGerarResumoLLM" class="mt-4 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                {{ erroGerarResumoLLM }}
              </p>

              <!-- Resultado do LLM -->
              <div v-if="resumoLLMResultado?.summary" class="mt-4 space-y-4">
                <p class="text-slate-800">
                  {{ resumoLLMResultado.summary.overview }}
                </p>

                <div class="grid gap-3 md:grid-cols-3">
                  <div class="rounded-xl bg-white p-4 ring-1 ring-amber-100">
                    <p class="text-xs font-black uppercase tracking-[0.2em] text-amber-700">Tendências</p>
                    <ul class="mt-3 space-y-2 text-sm text-slate-700">
                      <li v-for="item in resumoLLMResultado.summary.trends || []" :key="item">{{ item }}</li>
                    </ul>
                  </div>

                  <div class="rounded-xl bg-white p-4 ring-1 ring-amber-100">
                    <p class="text-xs font-black uppercase tracking-[0.2em] text-amber-700">Alertas</p>
                    <ul class="mt-3 space-y-2 text-sm text-slate-700">
                      <li v-for="item in resumoLLMResultado.summary.alerts || []" :key="item">{{ item }}</li>
                    </ul>
                  </div>

                  <div class="rounded-xl bg-white p-4 ring-1 ring-amber-100">
                    <p class="text-xs font-black uppercase tracking-[0.2em] text-amber-700">Recomendações</p>
                    <ul class="mt-3 space-y-2 text-sm text-slate-700">
                      <li v-for="item in resumoLLMResultado.summary.recommendations || []" :key="item">{{ item }}</li>
                    </ul>
                  </div>
                </div>

                <div class="flex flex-col gap-2 rounded-xl bg-white px-4 py-3 text-xs text-slate-600 ring-1 ring-amber-100 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
                  <span><strong class="text-slate-900">Confiança:</strong> {{ resumoLLMResultado.summary.confidence || 'media' }}</span>
                  <span><strong class="text-slate-900">Testes analisados:</strong> {{ resumoLLMResultado.testsAnalyzed || 0 }}</span>
                  <span><strong class="text-slate-900">Fonte:</strong> {{ resumoLLMResultado.source || 'local' }}</span>
                  <span v-if="resumoLLMResultado.model"><strong class="text-slate-900">Modelo:</strong> {{ resumoLLMResultado.model }}</span>
                </div>

                <p class="text-xs text-slate-500">
                  {{ resumoLLMResultado.summary.disclaimer || 'Resumo automatizado de apoio ao medico.' }}
                </p>
              </div>
            </div>

            <!-- Médico: Diagnóstico -->
            <div class="bg-white rounded-2xl border border-blue-200 p-5">
              <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p class="text-xs font-black uppercase tracking-[0.25em] text-blue-700">Diagnóstico médico</p>
                  <h4 class="mt-1 text-lg font-bold text-slate-900">Registrar diagnóstico</h4>
                  <p class="text-sm text-slate-600 mt-1">Digite o diagnóstico para este paciente.</p>
                </div>
              </div>

              <div class="mt-4 space-y-3">
                <textarea
                  v-model="textoDiagnostico"
                  placeholder="Digite aqui o diagnóstico do paciente..."
                  class="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-blue-500 focus:border-blue-500 text-slate-900 min-h-[120px] resize-y"
                ></textarea>

                <div class="flex items-center gap-3">
                  <button
                    @click="salvarDiagnosticoMedico"
                    :disabled="salvandoDiagnostico || !textoDiagnostico.trim()"
                    class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-xl font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {{ salvandoDiagnostico ? 'Salvando...' : 'Salvar diagnóstico' }}
                  </button>
                </div>

                <p v-if="erroSalvarDiagnostico" class="text-sm font-medium text-red-700 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
                  {{ erroSalvarDiagnostico }}
                </p>

                <p v-if="diagnosticoSalvo" class="text-sm font-medium text-green-700 bg-green-50 border border-green-100 rounded-xl px-4 py-3">
                  Diagnóstico salvo com sucesso em {{ formatarDataHora(diagnosticoSalvo.updatedAtIso) }}.
                </p>
              </div>
            </div>

            <!-- Médico: Publicar para o paciente -->
            <div class="bg-white rounded-2xl border border-emerald-200 p-5">
              <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p class="text-xs font-black uppercase tracking-[0.25em] text-emerald-700">Disponibilizar para o paciente</p>
                  <h4 class="mt-1 text-lg font-bold text-slate-900">Publicar resumo e diagnóstico</h4>
                  <p class="text-sm text-slate-600 mt-1">Após gerar o resumo LLM e salvar o diagnóstico, disponibilize para o paciente visualizar no perfil dele.</p>
                </div>
                <div class="flex flex-col items-end gap-2">
                  <button
                    @click="publicarResumoMedico"
                    :disabled="publicandoResumo || !resumoLLMResultado"
                    class="rounded-full bg-emerald-600 px-5 py-2 text-sm font-bold text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {{ publicandoResumo ? 'Publicando...' : 'Disponibilizar para paciente' }}
                  </button>
                  <p v-if="!resumoLLMResultado" class="text-xs text-slate-500">
                    Gere o resumo LLM primeiro.
                  </p>
                </div>
              </div>

              <div v-if="publicandoResumo" class="mt-4 flex items-center gap-3 rounded-xl bg-emerald-50/80 px-4 py-3 text-sm text-slate-600">
                <div class="h-4 w-4 animate-spin rounded-full border-2 border-slate-200 border-t-emerald-600"></div>
                Publicando para o paciente...
              </div>

              <p v-if="erroPublicarResumo" class="mt-4 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                {{ erroPublicarResumo }}
              </p>

              <div v-if="resumoPublicado && sumarioPublicacao" class="mt-4 rounded-xl border border-green-100 bg-green-50 px-4 py-3 text-sm text-green-800">
                <p class="font-bold">✅ Publicado com sucesso!</p>
                <p v-if="sumarioPublicacao.summaryAvailable">Resumo LLM disponibilizado para o paciente.</p>
                <p v-if="sumarioPublicacao.diagnosisAvailable">Diagnóstico disponibilizado para o paciente.</p>
                <p class="mt-1 text-xs text-green-600">Publicado em {{ formatarDataHora(sumarioPublicacao.publishedAtIso) }}</p>
              </div>
            </div>

            <!-- Médico: Histórico de testes do paciente -->
            <div class="bg-slate-50 rounded-2xl border border-slate-200 p-5">
              <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 class="text-xl font-bold text-slate-900">Histórico de testes</h3>
                  <p class="text-sm text-slate-600">{{ pacienteSelecionado.patientEmail }}</p>
                </div>
                <div class="text-sm text-slate-500">
                  {{ testesPacienteSelecionado.length }} teste(s) exibido(s)
                </div>
              </div>

              <p v-if="erroTestesPaciente" class="mt-4 text-sm font-medium text-red-700 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
                {{ erroTestesPaciente }}
              </p>

              <div v-else-if="carregandoTestesPaciente" class="mt-4 flex items-center justify-center py-10 bg-white rounded-xl border border-dashed border-slate-300">
                <div class="animate-spin rounded-full h-8 w-8 border-4 border-slate-200 border-t-emerald-600"></div>
              </div>

              <div v-else-if="testesPacienteSelecionado.length" class="mt-4">
                <DiagnosticHistoryPanel
                  :records="testesPacienteSelecionado"
                  @download-json="baixarHistoricoPacienteSelecionado"
                  @rerun="recarregarHistoricoPacienteSelecionado"
                />
              </div>

              <div v-else class="mt-4 flex flex-col items-center justify-center py-10 bg-white rounded-xl border border-dashed border-slate-300 text-center">
                <span class="text-4xl mb-3">🗂️</span>
                <p class="text-lg font-bold text-slate-900">Nenhum teste encontrado</p>
                <p class="text-sm text-slate-600 mt-1">Esse paciente ainda não possui histórico registrado.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- ==================== SEÇÃO DO PACIENTE ==================== -->

        <!-- Meu Resumo de Saúde (para pacientes) -->
        <div v-if="cargoEhPaciente" class="bg-white rounded-2xl shadow-md p-8 border border-slate-200">
          <div class="flex items-start justify-between gap-4 mb-6">
            <div>
              <h2 class="text-2xl font-bold text-slate-900">Resumo de Saúde</h2>
              <p class="text-slate-600 mt-2">Resumo gerado pelo seu médico com base nos seus testes cognitivos.</p>
            </div>
            <div>
              <div v-if="resumoDisponivel" class="text-sm font-semibold text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-full px-4 py-2">
                Disponível
              </div>
              <div v-else class="text-sm font-semibold text-slate-500 bg-slate-50 border border-slate-200 rounded-full px-4 py-2">
                Aguardando médico
              </div>
            </div>
          </div>

          <div v-if="carregandoResumoPacienteProprio" class="flex items-center justify-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-300">
            <div class="animate-spin rounded-full h-8 w-8 border-4 border-slate-200 border-t-emerald-600"></div>
          </div>

          <div v-else-if="erroResumoPacienteProprio" class="text-sm font-medium text-red-700 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
            {{ erroResumoPacienteProprio }}
          </div>

          <!-- Sem resumo disponível -->
          <div v-else-if="!resumoDisponivel" class="flex flex-col items-center justify-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-300 text-center">
            <span class="text-4xl mb-3">📋</span>
            <p class="text-lg font-bold text-slate-900">Nenhum resumo disponível ainda</p>
            <p class="text-sm text-slate-600 mt-1 max-w-md">
              Seu médico ainda não disponibilizou o resumo de saúde. Quando ele gerar e publicar, ele aparecerá aqui.
            </p>
          </div>

          <!-- Resumo disponível -->
          <div v-else-if="resumoPaciente?.summary" class="space-y-4">
            <div class="rounded-2xl border border-amber-200 bg-amber-50 p-5">
              <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p class="text-xs font-black uppercase tracking-[0.25em] text-amber-700">Resumo automático</p>
                  <h4 class="mt-1 text-lg font-bold text-slate-900">Leitura clínica do seu histórico</h4>
                </div>
                <div class="flex flex-col items-start gap-1 text-xs text-slate-600 sm:items-end">
                  <span class="rounded-full bg-white px-3 py-1 font-bold text-amber-700 ring-1 ring-amber-200">
                    {{ resumoPaciente.source === 'llm' ? 'LLM' : 'Fallback local' }}
                  </span>
                </div>
              </div>

              <div class="mt-4 space-y-4">
                <p class="text-slate-800">{{ resumoPaciente.summary.overview }}</p>

                <div class="grid gap-3 md:grid-cols-3">
                  <div class="rounded-xl bg-white p-4 ring-1 ring-amber-100">
                    <p class="text-xs font-black uppercase tracking-[0.2em] text-amber-700">Tendências</p>
                    <ul class="mt-3 space-y-2 text-sm text-slate-700">
                      <li v-for="item in resumoPaciente.summary.trends || []" :key="item">{{ item }}</li>
                    </ul>
                  </div>

                  <div class="rounded-xl bg-white p-4 ring-1 ring-amber-100">
                    <p class="text-xs font-black uppercase tracking-[0.2em] text-amber-700">Alertas</p>
                    <ul class="mt-3 space-y-2 text-sm text-slate-700">
                      <li v-for="item in resumoPaciente.summary.alerts || []" :key="item">{{ item }}</li>
                    </ul>
                  </div>

                  <div class="rounded-xl bg-white p-4 ring-1 ring-amber-100">
                    <p class="text-xs font-black uppercase tracking-[0.2em] text-amber-700">Recomendações</p>
                    <ul class="mt-3 space-y-2 text-sm text-slate-700">
                      <li v-for="item in resumoPaciente.summary.recommendations || []" :key="item">{{ item }}</li>
                    </ul>
                  </div>
                </div>

                <div class="flex flex-col gap-2 rounded-xl bg-white px-4 py-3 text-xs text-slate-600 ring-1 ring-amber-100 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
                  <span><strong class="text-slate-900">Confiança:</strong> {{ resumoPaciente.summary.confidence || 'media' }}</span>
                  <span><strong class="text-slate-900">Testes analisados:</strong> {{ resumoPaciente.testsAnalyzed || 0 }}</span>
                  <span v-if="resumoPaciente.generatedAtIso"><strong class="text-slate-900">Gerado em:</strong> {{ formatarDataHora(resumoPaciente.generatedAtIso) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Diagnóstico Médico (para pacientes) -->
        <div v-if="cargoEhPaciente && resumoDisponivel" class="bg-white rounded-2xl shadow-md p-8 border border-slate-200">
          <div class="flex items-start justify-between gap-4 mb-6">
            <div>
              <h2 class="text-2xl font-bold text-slate-900">Diagnóstico Médico</h2>
              <p class="text-slate-600 mt-2">Diagnóstico registrado pelo seu médico.</p>
            </div>
          </div>

          <div v-if="resumoPaciente?.diagnosis" class="rounded-2xl border border-blue-200 bg-blue-50 p-5">
            <div class="flex items-start gap-3">
              <div class="text-2xl">🩺</div>
              <div class="flex-1">
                <p class="text-xs font-black uppercase tracking-[0.25em] text-blue-700 mb-2">Diagnóstico</p>
                <p class="text-slate-800 whitespace-pre-wrap">{{ resumoPaciente.diagnosis }}</p>
                <p v-if="resumoPaciente.diagnosisDoctorName" class="mt-3 text-xs text-slate-500">
                  Dr(a). {{ resumoPaciente.diagnosisDoctorName }}
                </p>
              </div>
            </div>
          </div>

          <div v-else class="flex flex-col items-center justify-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-300 text-center">
            <span class="text-4xl mb-3">🩺</span>
            <p class="text-lg font-bold text-slate-900">Nenhum diagnóstico disponível</p>
            <p class="text-sm text-slate-600 mt-1">Seu médico ainda não registrou um diagnóstico.</p>
          </div>
        </div>

        <!-- Meus Médicos (para pacientes) -->
        <div v-if="cargoEhPaciente" class="bg-white rounded-2xl shadow-md p-8 border border-slate-200">
          <div class="flex items-start justify-between gap-4 mb-6">
            <div>
              <h2 class="text-2xl font-bold text-slate-900">Meus médicos</h2>
              <p class="text-slate-600 mt-2">Profissionais de saúde vinculados ao seu perfil.</p>
            </div>
            <div class="text-sm font-semibold text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-full px-4 py-2">
              {{ meusMedicos.length }} vinculado(s)
            </div>
          </div>

          <div v-if="carregandoMeusMedicos" class="flex items-center justify-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-300">
            <div class="animate-spin rounded-full h-8 w-8 border-4 border-slate-200 border-t-emerald-600"></div>
          </div>

          <div v-else-if="erroMeusMedicos" class="text-sm font-medium text-red-700 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
            {{ erroMeusMedicos }}
          </div>

          <div v-else-if="meusMedicos.length === 0" class="flex flex-col items-center justify-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-300 text-center">
            <span class="text-4xl mb-3">👨‍⚕️</span>
            <p class="text-lg font-bold text-slate-900">Nenhum médico vinculado</p>
            <p class="text-sm text-slate-600 mt-1">Vá em "Editar Perfil" para buscar e solicitar vínculo com um profissional.</p>
            <button
              @click="router.push('/profile/edit')"
              class="mt-4 bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2 rounded-xl font-bold transition-all"
            >
              Buscar médico
            </button>
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div
              v-for="medico in meusMedicos"
              :key="medico.doctorUid"
              class="flex items-start gap-4 rounded-xl border border-slate-200 bg-slate-50 p-4"
            >
              <div class="w-12 h-12 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-xl flex items-center justify-center text-lg flex-shrink-0">
                👨‍⚕️
              </div>
              <div class="flex-1 min-w-0">
                <p class="font-bold text-slate-900 truncate">{{ medico.doctorName }}</p>
                <p class="text-sm text-slate-600 truncate">{{ medico.doctorEmail }}</p>
                <div v-if="medico.doctorEspecialidade || medico.doctorInstituicao" class="mt-1 flex flex-wrap gap-2">
                  <span v-if="medico.doctorEspecialidade" class="inline-block text-xs font-medium bg-blue-50 text-blue-700 rounded-full px-2 py-0.5">
                    {{ medico.doctorEspecialidade }}
                  </span>
                  <span v-if="medico.doctorInstituicao" class="inline-block text-xs font-medium bg-purple-50 text-purple-700 rounded-full px-2 py-0.5">
                    {{ medico.doctorInstituicao }}
                  </span>
                </div>
                <div v-if="medico.doctorCrmcrp" class="mt-1 text-xs text-slate-500">
                  {{ medico.doctorCrmcrp }}
                </div>
                <p v-if="medico.linkedAtIso" class="mt-1 text-xs text-slate-400">
                  Vinculado em {{ formatarDataHora(medico.linkedAtIso) }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Settings Section -->
        <div class="bg-white rounded-2xl shadow-md p-8 border border-slate-200">
          <h2 class="text-2xl font-bold text-slate-900 mb-6">Configurações da Conta</h2>
          
          <div class="space-y-4">
            <div v-if="userData?.cargo !== 'especialista'" class="space-y-2">
              <button @click="abrirHistorico" class="w-full text-left p-4 bg-slate-50 rounded-xl border border-slate-200 hover:bg-slate-100 transition-colors">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="font-medium text-slate-900">Histórico de testes</p>
                    <p class="text-sm text-slate-600">Ver seus testes anteriores</p>
                  </div>
                  <span class="text-xl">→</span>
                </div>
              </button>

              <button @click="router.push('/profile/edit')" class="w-full text-left p-4 bg-slate-50 rounded-xl border border-slate-200 hover:bg-slate-100 transition-colors">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="font-medium text-slate-900">Editar Perfil</p>
                    <p class="text-sm text-slate-600">Onde fica o vínculo com o médico</p>
                  </div>
                  <span class="text-xl">→</span>
                </div>
              </button>

              <button @click="showNotifications = true" class="w-full text-left p-4 bg-slate-50 rounded-xl border border-slate-200 hover:bg-slate-100 transition-colors">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="font-medium text-slate-900">Notificações</p>
                    <p class="text-sm text-slate-600">Gerenciar preferências de notificações</p>
                  </div>
                  <span class="text-xl">→</span>
                </div>
              </button>

              <button @click="abrirPrivacidadeSeguranca" class="w-full text-left p-4 bg-slate-50 rounded-xl border border-slate-200 hover:bg-slate-100 transition-colors">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="font-medium text-slate-900">Privacidade e Segurança</p>
                    <p class="text-sm text-slate-600">Controle sua privacidade de dados</p>
                  </div>
                  <span class="text-xl">→</span>
                </div>
              </button>
            </div>

            <div v-else class="space-y-2">
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

              <div class="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200 hover:bg-slate-100 transition-colors cursor-pointer" @click="abrirPrivacidadeSeguranca">
                <div>
                  <p class="font-medium text-slate-900">Privacidade e Segurança</p>
                  <p class="text-sm text-slate-600">Controle sua privacidade de dados</p>
                </div>
                <span class="text-xl">→</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Notifications modal -->
        <div v-if="showNotifications" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div class="bg-white rounded-2xl p-6 w-full max-w-md">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-bold">Notificações</h3>
              <button @click="showNotifications = false" class="text-slate-500">Fechar</button>
            </div>
            <p class="text-sm text-slate-600">Configurações de notificações serão adicionadas aqui. Por enquanto você verá alertas no app.</p>
            <div class="mt-4 flex justify-end">
              <button @click="showNotifications = false" class="px-4 py-2 bg-emerald-600 text-white rounded-lg">Ok</button>
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
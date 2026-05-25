<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import DiagnosticHistoryPanel from '../components/diagnostics/DiagnosticHistoryPanel.vue'
import { carregarHistoricoTestes, formatarResultadoTeste, getFeedbackForResult } from '../services/testResults'
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

const toNumber = (value) => {
  const numericValue = Number(value)
  return Number.isFinite(numericValue) ? numericValue : 0
}

const formatDate = (value) => {
  if (!value) return 'Sem data'
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

const formatDateOnly = (value) => {
  if (!value) return 'Sem data'
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(new Date(value))
}

const formatDuration = (value) => {
  const totalMs = Math.max(0, Math.round(toNumber(value)))

  if (totalMs < 1000) {
    return `${totalMs} ms`
  }

  const totalSeconds = Math.round(totalMs / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60

  if (!minutes) {
    return `${totalSeconds}s`
  }

  return `${minutes}m ${String(seconds).padStart(2, '0')}s`
}

const formatMetricValue = (metricKey, value) => {
  if (metricKey === 'accuracyPercent') {
    return `${Math.round(toNumber(value))}%`
  }

  if (metricKey === 'completionTimeMs' || metricKey === 'averageLatencyMs') {
    return formatDuration(value)
  }

  return `${Math.round(toNumber(value))}`
}

const getTestDefinition = (testType) => {
  const definitions = {
    'n-back-2': {
      label: 'Memória de curto prazo',
      accent: 'emerald',
      metricKey: 'accuracyPercent',
      betterWhenHigher: true,
      getValue: (record) => toNumber(record.accuracyPercent ?? record.summary?.accuracyPercent ?? 0),
      getSecondary: (record) => ([
        { label: 'Latência média', value: formatDuration(record.averageLatencyMs ?? record.summary?.averageLatencyMs) },
        { label: 'Erros', value: String(toNumber(record.incorrectResponses ?? record.summary?.incorrectResponses)) },
      ]),
    },
    'fluencia-semantica': {
      label: 'Fluência semântica',
      accent: 'amber',
      metricKey: 'totalCorrect',
      betterWhenHigher: true,
      getValue: (record) => toNumber(record.totalCorrect ?? record.summary?.totalCorrect ?? 0),
      getSecondary: (record) => ([
        { label: 'Intrusões', value: String(toNumber(record.totalIntrusions ?? record.summary?.totalIntrusions)) },
        { label: 'Perseverações', value: String(toNumber(record.totalPerseverations ?? record.summary?.totalPerseverations)) },
      ]),
    },
    'trail-b': {
      label: 'Atenção alternada',
      accent: 'violet',
      metricKey: 'completionTimeMs',
      betterWhenHigher: false,
      getValue: (record) => toNumber(record.completionTimeMs ?? record.summary?.completionTimeMs ?? 0),
      getSecondary: (record) => ([
        { label: 'Erros', value: String(toNumber(record.errorCount ?? record.summary?.errorCount)) },
        { label: 'Passos corretos', value: String(toNumber(record.correctSteps ?? record.summary?.correctSteps)) },
      ]),
    },
  }

  return definitions[testType] || {
    label: 'Teste cognitivo',
    accent: 'slate',
    metricKey: 'accuracyPercent',
    betterWhenHigher: true,
    getValue: (record) => toNumber(record.accuracyPercent ?? record.summary?.accuracyPercent ?? 0),
    getSecondary: () => [],
  }
}

const historicoOrdenado = computed(() => (
  [...registros.value].sort((a, b) => toNumber(a.createdAtMs) - toNumber(b.createdAtMs))
))

const dashboardSummary = computed(() => {
  const historico = historicoOrdenado.value

  if (!historico.length) {
    return null
  }

  const primeiro = historico[0]
  const ultimo = historico[historico.length - 1]
  const ultimoFeedback = getFeedbackForResult(ultimo)?.feedback || null

  return {
    totalTestes: historico.length,
    tiposAcompanhados: new Set(historico.map((registro) => registro.testType)).size,
    periodo: `${formatDateOnly(primeiro.createdAtMs)} até ${formatDateOnly(ultimo.createdAtMs)}`,
    ultimoTeste: ultimo.testName || getTestDefinition(ultimo.testType).label,
    ultimoTesteData: ultimo.createdAtMs,
    ultimoFeedback,
  }
})

const evolutionCards = computed(() => {
  const historico = historicoOrdenado.value
  const groupedByType = historico.reduce((accumulator, record) => {
    const testType = record.testType || 'teste'
    if (!accumulator[testType]) {
      accumulator[testType] = []
    }
    accumulator[testType].push(record)
    return accumulator
  }, {})

  return Object.entries(groupedByType)
    .map(([testType, records]) => {
      const definition = getTestDefinition(testType)
      const orderedRecords = [...records].sort((a, b) => toNumber(a.createdAtMs) - toNumber(b.createdAtMs))
      const latest = orderedRecords[orderedRecords.length - 1]
      const previous = orderedRecords[orderedRecords.length - 2] || null
      const latestValue = definition.getValue(latest)
      const previousValue = previous ? definition.getValue(previous) : null
      const delta = previousValue === null ? null : latestValue - previousValue
      const improved = delta === null ? null : (definition.betterWhenHigher ? delta >= 0 : delta <= 0)
      const recentValues = orderedRecords.slice(-6).map((item) => definition.getValue(item))
      const minValue = Math.min(...recentValues)
      const maxValue = Math.max(...recentValues)
      const sparkline = recentValues.map((value) => {
        if (recentValues.length === 1 || maxValue === minValue) {
          return 60
        }

        return 18 + ((value - minValue) / (maxValue - minValue)) * 82
      })

      const deltaValue = delta === null ? 'Primeira medição' : `${improved ? 'Melhora' : 'Piora'} de ${formatMetricValue(definition.metricKey, Math.abs(delta))}`

      return {
        testType,
        label: definition.label,
        accent: definition.accent,
        displayValue: formatMetricValue(definition.metricKey, latestValue),
        trendLabel: delta === null ? 'Primeira medição' : improved ? 'Melhora' : 'Piora',
        trendValue: deltaValue,
        trendClass: delta === null ? 'bg-slate-500/15 text-slate-200 ring-slate-400/20' : improved ? 'bg-emerald-500/15 text-emerald-200 ring-emerald-400/30' : 'bg-rose-500/15 text-rose-200 ring-rose-400/30',
        barClass: definition.accent === 'emerald'
          ? 'bg-emerald-400'
          : definition.accent === 'amber'
            ? 'bg-amber-400'
            : definition.accent === 'violet'
              ? 'bg-violet-400'
              : 'bg-slate-400',
        sparkline,
        secondary: definition.getSecondary(latest),
        lastDate: latest.createdAtMs,
      }
    })
    .sort((a, b) => toNumber(b.lastDate) - toNumber(a.lastDate))
})

const feedbackToneClass = (category) => {
  switch (category) {
    case 'normal':
      return 'bg-emerald-500/15 text-emerald-200 ring-emerald-400/30'
    case 'monitor':
      return 'bg-amber-500/15 text-amber-200 ring-amber-400/30'
    case 'procurar_medico':
      return 'bg-orange-500/15 text-orange-200 ring-orange-400/30'
    case 'urgencia':
      return 'bg-red-500/15 text-red-200 ring-red-400/30'
    default:
      return 'bg-slate-500/15 text-slate-200 ring-slate-400/20'
  }
}

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
      <div class="mb-6">
        <button @click="router.push('/profile')" class="text-slate-500 hover:text-emerald-600 flex items-center gap-2 transition-colors font-medium">
          <span>←</span> Voltar para o Perfil
        </button>
      </div>
      
      <div class="bg-white rounded-2xl shadow-md p-8 border border-slate-200">
        <h1 class="text-2xl font-bold text-slate-900 mb-2">Histórico de Testes</h1>
        <p class="text-slate-600 mb-6">Lista completa dos testes realizados por você.</p>

        <section v-if="registros.length" class="mb-6 overflow-hidden rounded-3xl border border-slate-800 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 p-6 sm:p-8 text-white shadow-xl">
          <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div class="max-w-2xl">
              <p class="text-xs font-black uppercase tracking-[0.35em] text-emerald-300">Dashboard de evolução</p>
              <h2 class="mt-3 text-3xl font-black tracking-tight sm:text-4xl">Evolução do paciente</h2>
              <p class="mt-3 text-sm leading-6 text-slate-300">Resumo longitudinal dos últimos exames para acompanhar precisão, tempo de resposta e estabilidade clínica ao longo do tratamento.</p>
            </div>

            <div v-if="dashboardSummary" class="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 backdrop-blur">
              <p class="text-xs uppercase tracking-[0.25em] text-slate-400">Última avaliação</p>
              <p class="mt-1 text-lg font-bold text-white">{{ dashboardSummary.ultimoTeste }}</p>
              <p class="mt-1 text-sm text-slate-300">{{ formatDate(dashboardSummary.ultimoTesteData) }}</p>
              <p v-if="dashboardSummary.ultimoFeedback" :class="`mt-3 inline-flex rounded-full px-3 py-1 text-xs font-bold ring-1 ${feedbackToneClass(dashboardSummary.ultimoFeedback.category)}`">
                {{ dashboardSummary.ultimoFeedback.shortMessage }}
              </p>
            </div>
          </div>

          <div v-if="dashboardSummary" class="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <article class="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p class="text-xs uppercase tracking-[0.25em] text-slate-400">Testes registrados</p>
              <p class="mt-3 text-3xl font-black text-white">{{ dashboardSummary.totalTestes }}</p>
              <p class="mt-2 text-sm text-slate-300">Exames disponíveis para análise longitudinal.</p>
            </article>

            <article class="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p class="text-xs uppercase tracking-[0.25em] text-slate-400">Tipos acompanhados</p>
              <p class="mt-3 text-3xl font-black text-white">{{ dashboardSummary.tiposAcompanhados }}</p>
              <p class="mt-2 text-sm text-slate-300">Memória, fluência e atenção alternada.</p>
            </article>

            <article class="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p class="text-xs uppercase tracking-[0.25em] text-slate-400">Período observado</p>
              <p class="mt-3 text-lg font-black text-white">{{ dashboardSummary.periodo }}</p>
              <p class="mt-2 text-sm text-slate-300">Linha do tempo consolidada das sessões.</p>
            </article>

            <article class="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p class="text-xs uppercase tracking-[0.25em] text-slate-400">Situação atual</p>
              <p v-if="dashboardSummary.ultimoFeedback" :class="`mt-3 inline-flex rounded-full px-3 py-1 text-xs font-bold ring-1 ${feedbackToneClass(dashboardSummary.ultimoFeedback.category)}`">
                {{ dashboardSummary.ultimoFeedback.category.replace('_', ' ') }}
              </p>
              <p class="mt-2 text-sm text-slate-300">
                {{ dashboardSummary.ultimoFeedback?.detailedMessage || 'Sem feedback disponível para a última sessão.' }}
              </p>
            </article>
          </div>

          <div v-if="evolutionCards.length" class="mt-6 grid gap-4 lg:grid-cols-3">
            <article v-for="card in evolutionCards" :key="card.testType" class="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="text-xs uppercase tracking-[0.3em] text-slate-400">{{ card.label }}</p>
                  <p class="mt-2 text-3xl font-black text-white">{{ card.displayValue }}</p>
                </div>

                <span :class="`rounded-full px-3 py-1 text-xs font-bold ring-1 ${card.trendClass}`">{{ card.trendLabel }}</span>
              </div>

              <p class="mt-3 text-sm text-slate-300">{{ card.trendValue }}</p>

              <div class="mt-5 flex h-20 items-end gap-2">
                <span
                  v-for="(barHeight, index) in card.sparkline"
                  :key="`${card.testType}-bar-${index}`"
                  :class="`flex-1 rounded-t-full ${card.barClass}`"
                  :style="{ height: `${barHeight}%`, minHeight: '10%' }"
                />
              </div>

              <div class="mt-4 flex flex-wrap gap-2">
                <span
                  v-for="metric in card.secondary"
                  :key="`${card.testType}-${metric.label}`"
                  class="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-slate-200"
                >
                  {{ metric.label }} · {{ metric.value }}
                </span>
              </div>

              <p class="mt-4 text-xs uppercase tracking-[0.25em] text-slate-400">Última sessão em {{ formatDate(card.lastDate) }}</p>
            </article>
          </div>
        </section>

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

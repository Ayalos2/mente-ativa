<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import DiagnosticShell from '../components/diagnostics/DiagnosticShell.vue'
import { memoryStimuli, shuffleArray, diagnosticRoutes } from '../data/diagnosticTests'
import { useDiagnosticTestStore } from '../stores/diagnosticTestStore'
import { getCurrentUserProfile } from '../services/sessionUser'
import { salvarResultadoTeste } from '../services/testResults'
import { downloadJson } from '../utils/downloadJson'

const router = useRouter()
const store = useDiagnosticTestStore()

const testId = 'n-back-2'
const testName = 'Teste de Memória de Curto Prazo (N-Back Adaptado)'
const testType = 'n-back-2'
const nBackDepth = 2
const sequenceLength = 14

const phase = ref('ready')
const sequence = ref([])
const currentIndex = ref(0)
const responseDetails = ref([])
const currentFeedback = ref('')
const feedbackTone = ref('emerald')
const currentExport = ref(null)
const trialStartMs = ref(0)
let nextTrialTimeout = null

const currentItem = computed(() => sequence.value[currentIndex.value] || null)
const expectedMatch = computed(() => currentIndex.value >= nBackDepth && currentItem.value?.id === sequence.value[currentIndex.value - nBackDepth]?.id)
const totalResponses = computed(() => responseDetails.value.length)
const correctResponses = computed(() => responseDetails.value.filter((entry) => entry.correct).length)
const incorrectResponses = computed(() => totalResponses.value - correctResponses.value)
const accuracyPercent = computed(() => (totalResponses.value ? Math.round((correctResponses.value / totalResponses.value) * 100) : 0))
const latencies = computed(() => responseDetails.value.map((entry) => entry.latencyMs))
const averageLatencyMs = computed(() => (latencies.value.length ? Math.round(latencies.value.reduce((acc, value) => acc + value, 0) / latencies.value.length) : 0))
const medianLatencyMs = computed(() => {
  if (!latencies.value.length) return 0
  const sorted = [...latencies.value].sort((a, b) => a - b)
  const middle = Math.floor(sorted.length / 2)
  return sorted.length % 2 === 0 ? Math.round((sorted[middle - 1] + sorted[middle]) / 2) : sorted[middle]
})
const falsePositives = computed(() => responseDetails.value.filter((entry) => entry.answer === true && entry.expectedMatch === false).length)
const falseNegatives = computed(() => responseDetails.value.filter((entry) => entry.answer === false && entry.expectedMatch === true).length)
const completionLabel = computed(() => (accuracyPercent.value >= 80 ? 'Padrão estável' : 'Sinal de atenção'))

const buildSequence = () => {
  const basePool = shuffleArray(memoryStimuli)
  const generated = []

  while (generated.length < sequenceLength) {
    const canRepeatTwoBack = generated.length >= nBackDepth && Math.random() < 0.45

    if (canRepeatTwoBack) {
      generated.push({ ...generated[generated.length - nBackDepth], target: true })
      continue
    }

    const recentIds = generated.slice(-nBackDepth).map((item) => item.id)
    const candidatePool = basePool.filter((item) => !recentIds.includes(item.id))
    const nextItem = candidatePool[Math.floor(Math.random() * candidatePool.length)] || basePool[generated.length % basePool.length]
    generated.push({ ...nextItem, target: false })
  }

  sequence.value = generated
}

const startTest = () => {
  store.startSession({
    testId,
    testName,
    testType,
    userProfile: getCurrentUserProfile(),
    metadata: { nBackDepth, sequenceLength },
  })

  buildSequence()
  responseDetails.value = []
  currentFeedback.value = 'Observe o item e responda se ele é igual ao de dois turnos atrás.'
  feedbackTone.value = 'emerald'
  currentIndex.value = 0
  trialStartMs.value = Date.now()
  phase.value = 'running'
}

const finishTest = async () => {
  phase.value = 'result'

  const summary = {
    totalResponses: totalResponses.value,
    correctResponses: correctResponses.value,
    incorrectResponses: incorrectResponses.value,
    accuracyPercent: accuracyPercent.value,
    averageLatencyMs: averageLatencyMs.value,
    medianLatencyMs: medianLatencyMs.value,
    falsePositives: falsePositives.value,
    falseNegatives: falseNegatives.value,
    nBackDepth,
    completionLabel: completionLabel.value,
  }

  const exportPayload = store.finishSession(summary, { sequence: [...sequence.value], responseDetails: [...responseDetails.value] })
  currentExport.value = exportPayload

  await salvarResultadoTeste({
    testId,
    testName,
    testType,
    summary,
    clickLogs: store.state.clickLogs,
    responseLogs: store.state.responseLogs,
    exportPayload,
    structuredData: { sequence: [...sequence.value], responseDetails: [...responseDetails.value] },
    userProfile: getCurrentUserProfile(),
  })
}

const handleAnswer = (answer) => {
  if (phase.value !== 'running' || !currentItem.value) {
    return
  }

  const latencyMs = Date.now() - trialStartMs.value
  const expected = Boolean(expectedMatch.value)
  const correct = answer === expected

  const clickLog = store.logClick({
    testId,
    testName,
    testType,
    itemId: currentItem.value.id,
    itemLabel: currentItem.value.label,
    stepIndex: currentIndex.value,
    expected,
    answer,
    correct,
    latencyMs,
  })

  const responseEntry = store.logResponse({
    testId,
    testName,
    testType,
    itemId: currentItem.value.id,
    itemLabel: currentItem.value.label,
    stepIndex: currentIndex.value,
    expectedMatch: expected,
    answer,
    correct,
    latencyMs,
    clickLogId: clickLog.id,
  })

  responseDetails.value.push({
    ...responseEntry,
    itemId: currentItem.value.id,
    itemLabel: currentItem.value.label,
    expectedMatch: expected,
  })

  currentFeedback.value = correct
    ? 'Correto. O item atual corresponde ao de dois turnos atrás.'
    : 'Incorreto. Reavalie o item de dois turnos atrás e prossiga.'
  feedbackTone.value = correct ? 'emerald' : 'rose'

  if (currentIndex.value >= sequence.value.length - 1) {
    void finishTest()
    return
  }

  phase.value = 'feedback'
  clearTimeout(nextTrialTimeout)
  nextTrialTimeout = setTimeout(() => {
    currentIndex.value += 1
    phase.value = 'running'
    trialStartMs.value = Date.now()
    currentFeedback.value = 'Observe o próximo estímulo.'
  }, 650)
}

const downloadCurrentJson = () => {
  if (!currentExport.value) return
  downloadJson('mente-ativa-nback.json', currentExport.value)
}

const restart = () => {
  store.reset()
  sequence.value = []
  currentIndex.value = 0
  responseDetails.value = []
  currentExport.value = null
  currentFeedback.value = ''
  phase.value = 'ready'
}

onBeforeUnmount(() => {
  clearTimeout(nextTrialTimeout)
})
</script>

<template>
  <DiagnosticShell
    title="Teste de Memória de Curto Prazo"
    subtitle="Acompanhe se o estímulo atual é igual ao apresentado dois turnos atrás. O tempo de latência e a precisão servem como marcadores de atenção e memória de trabalho ao longo do acompanhamento longitudinal."
    eyebrow="N-Back adaptado"
    accent="emerald"
    @back="router.push('/testes')"
    @dashboard="router.push('/testes')"
  >
    <section class="grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
      <div class="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm text-slate-950">
        <template v-if="phase === 'ready'">
          <div class="space-y-5">
            <p class="text-lg sm:text-xl text-slate-700 leading-relaxed">Você verá uma sequência de palavras e ícones. Clique em <strong>Igual</strong> quando o item atual for idêntico ao de dois turnos atrás.</p>
            <div class="grid sm:grid-cols-3 gap-4">
              <div class="rounded-2xl bg-slate-100 p-4 border border-slate-200">
                <p class="text-sm font-bold text-slate-500">Nível</p>
                <p class="text-2xl font-black">2-Back</p>
              </div>
              <div class="rounded-2xl bg-slate-100 p-4 border border-slate-200">
                <p class="text-sm font-bold text-slate-500">Sequência</p>
                <p class="text-2xl font-black">{{ sequenceLength }} itens</p>
              </div>
              <div class="rounded-2xl bg-slate-100 p-4 border border-slate-200">
                <p class="text-sm font-bold text-slate-500">Métricas</p>
                <p class="text-2xl font-black">Latência + precisão</p>
              </div>
            </div>
            <button @click="startTest" class="rounded-2xl bg-emerald-600 px-6 py-4 font-black text-white hover:bg-emerald-700 text-xl">Iniciar sessão</button>
          </div>
        </template>

        <template v-else-if="phase === 'running' || phase === 'feedback'">
          <div class="space-y-6">
            <div class="flex items-center justify-between gap-3">
              <p class="text-sm font-black uppercase tracking-[0.2em] text-slate-500">Item {{ currentIndex + 1 }} de {{ sequence.length }}</p>
              <p class="text-sm font-black uppercase tracking-[0.2em] text-slate-500">Resposta correta: {{ expectedMatch ? 'Igual' : 'Diferente' }}</p>
            </div>

            <div class="rounded-3xl border-4 border-slate-200 bg-slate-950 p-8 sm:p-10 text-center shadow-lg">
              <p class="text-6xl sm:text-8xl mb-4">{{ currentItem?.icon }}</p>
              <p class="text-3xl sm:text-5xl font-black text-white tracking-tight">{{ currentItem?.label }}</p>
            </div>

            <div class="grid sm:grid-cols-2 gap-4">
              <button @click="handleAnswer(true)" class="rounded-3xl bg-emerald-600 px-6 py-5 text-2xl font-black text-white hover:bg-emerald-500">Igual</button>
              <button @click="handleAnswer(false)" class="rounded-3xl bg-slate-900 px-6 py-5 text-2xl font-black text-white hover:bg-slate-800">Diferente</button>
            </div>

            <div class="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-lg font-semibold text-emerald-900">
              {{ currentFeedback }}
            </div>
          </div>
        </template>

        <template v-else>
          <div class="space-y-6">
            <div class="rounded-3xl border border-slate-200 bg-slate-50 p-6">
              <p class="text-sm font-black uppercase tracking-[0.2em] text-slate-500">Sessão concluída</p>
              <h2 class="text-3xl font-black text-slate-950 mt-2">Resultado exportado em JSON</h2>
              <p class="text-slate-600 mt-3">Os registros de clique e a pontuação permitem comparar mudanças de latência e precisão ao longo das avaliações, útil para rastrear tendência de declínio cognitivo.</p>
            </div>

            <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div class="rounded-2xl border border-slate-200 p-4"><p class="text-sm font-bold text-slate-500">Precisão</p><p class="text-3xl font-black text-slate-950">{{ accuracyPercent }}%</p></div>
              <div class="rounded-2xl border border-slate-200 p-4"><p class="text-sm font-bold text-slate-500">Latência média</p><p class="text-3xl font-black text-slate-950">{{ averageLatencyMs }} ms</p></div>
              <div class="rounded-2xl border border-slate-200 p-4"><p class="text-sm font-bold text-slate-500">Falsos positivos</p><p class="text-3xl font-black text-slate-950">{{ falsePositives }}</p></div>
              <div class="rounded-2xl border border-slate-200 p-4"><p class="text-sm font-bold text-slate-500">Falsos negativos</p><p class="text-3xl font-black text-slate-950">{{ falseNegatives }}</p></div>
            </div>

            <div class="flex flex-wrap gap-3">
              <button @click="downloadCurrentJson" class="rounded-2xl bg-slate-950 px-5 py-3 font-black text-white hover:bg-slate-800">Baixar JSON</button>
              <button @click="restart" class="rounded-2xl border border-slate-300 px-5 py-3 font-black text-slate-950 hover:bg-slate-100">Novo teste</button>
            </div>
          </div>
        </template>
      </div>

      <aside class="space-y-4">
        <div class="rounded-3xl border border-slate-800 bg-slate-900 p-5 text-white">
          <p class="text-sm font-black uppercase tracking-[0.2em] text-slate-400">Resumo</p>
          <div class="mt-4 grid grid-cols-2 gap-3">
            <div class="rounded-2xl bg-slate-800 p-4"><p class="text-xs uppercase tracking-[0.2em] text-slate-400">Acertos</p><p class="text-3xl font-black">{{ correctResponses }}</p></div>
            <div class="rounded-2xl bg-slate-800 p-4"><p class="text-xs uppercase tracking-[0.2em] text-slate-400">Erros</p><p class="text-3xl font-black">{{ incorrectResponses }}</p></div>
          </div>
          <div class="mt-3 rounded-2xl bg-emerald-500/15 p-4 text-emerald-100">
            <p class="text-xs uppercase tracking-[0.2em] text-emerald-200">Comentário longitudinal</p>
            <p class="mt-2 text-sm leading-relaxed">A combinação de precisão e latência por item é sensível a lentificação cognitiva e pode ser comparada sessão a sessão para detectar piora funcional.</p>
          </div>
        </div>

        <div class="rounded-3xl border border-slate-200 bg-white p-5 text-slate-950 shadow-sm">
          <p class="text-sm font-black uppercase tracking-[0.2em] text-slate-500">Logs de clique</p>
          <div class="mt-4 max-h-[440px] overflow-auto space-y-3 pr-1">
            <div v-for="entry in store.state.clickLogs" :key="entry.id" class="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm">
              <p class="font-bold">{{ entry.itemLabel }}</p>
              <p class="text-slate-600">{{ entry.correct ? 'Acerto' : 'Erro' }} • {{ entry.latencyMs }} ms</p>
            </div>
          </div>
        </div>
      </aside>
    </section>
  </DiagnosticShell>
</template>

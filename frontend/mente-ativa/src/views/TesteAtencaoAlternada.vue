<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import DiagnosticShell from '../components/diagnostics/DiagnosticShell.vue'
import { diagnosticRoutes, trailSequence, shuffleArray } from '../data/diagnosticTests'
import { useDiagnosticTestStore } from '../stores/diagnosticTestStore'
import { getCurrentUserProfile } from '../services/sessionUser'
import { salvarResultadoTeste } from '../services/testResults'
import { downloadJson } from '../utils/downloadJson'

const router = useRouter()
const store = useDiagnosticTestStore()

const testId = 'trail-b'
const testName = 'Teste de Atenção Alternada (Trail Making Test - Parte B)'
const testType = 'trail-b'

const phase = ref('ready')
const board = ref([])
const currentExpectedIndex = ref(0)
const errorCount = ref(0)
const clickCount = ref(0)
const startedAtMs = ref(0)
const currentExport = ref(null)

const expectedToken = computed(() => trailSequence[currentExpectedIndex.value] || null)
const completionPercent = computed(() => Math.round((currentExpectedIndex.value / trailSequence.length) * 100))

const buildBoard = () => {
  board.value = shuffleArray(trailSequence)
}

const startTest = () => {
  store.startSession({
    testId,
    testName,
    testType,
    userProfile: getCurrentUserProfile(),
    metadata: { sequence: trailSequence.map((item) => item.label) },
  })

  buildBoard()
  currentExpectedIndex.value = 0
  errorCount.value = 0
  clickCount.value = 0
  currentExport.value = null
  startedAtMs.value = Date.now()
  phase.value = 'running'
}

const finishTest = async () => {
  phase.value = 'result'
  const completionTimeMs = Date.now() - startedAtMs.value

  const summary = {
    completionTimeMs,
    errorCount: errorCount.value,
    correctSteps: trailSequence.length - errorCount.value,
    totalClicks: clickCount.value,
    totalItems: trailSequence.length,
  }

  const exportPayload = store.finishSession(summary, {
    board: [...board.value],
    trailSequence: [...trailSequence],
  })
  currentExport.value = exportPayload

  await salvarResultadoTeste({
    testId,
    testName,
    testType,
    summary,
    clickLogs: store.state.clickLogs,
    responseLogs: store.state.responseLogs,
    exportPayload,
    structuredData: {
      board: [...board.value],
      trailSequence: [...trailSequence],
    },
    userProfile: getCurrentUserProfile(),
  })
}

const handleClick = (item) => {
  if (phase.value !== 'running' || !expectedToken.value) {
    return
  }

  clickCount.value += 1
  const correct = item.id === expectedToken.value.id

  store.logClick({
    testId,
    testName,
    testType,
    itemId: item.id,
    itemLabel: item.label,
    expected: expectedToken.value.id,
    answer: item.id,
    correct,
    sequenceIndex: currentExpectedIndex.value,
    latencyMs: Date.now() - startedAtMs.value,
  })

  store.logResponse({
    testId,
    testName,
    testType,
    itemId: item.id,
    itemLabel: item.label,
    expected: expectedToken.value.id,
    answer: item.id,
    correct,
    sequenceIndex: currentExpectedIndex.value,
    latencyMs: Date.now() - startedAtMs.value,
  })

  if (!correct) {
    errorCount.value += 1
    return
  }

  if (currentExpectedIndex.value >= trailSequence.length - 1) {
    void finishTest()
    return
  }

  currentExpectedIndex.value += 1
}

const downloadCurrentJson = () => {
  if (!currentExport.value) return
  downloadJson('mente-ativa-trail-b.json', currentExport.value)
}

const restart = () => {
  store.reset()
  currentExpectedIndex.value = 0
  errorCount.value = 0
  clickCount.value = 0
  currentExport.value = null
  phase.value = 'ready'
}
</script>

<template>
  <DiagnosticShell
    title="Teste de Atenção Alternada"
    subtitle="Clique nos itens em ordem alternada entre números e letras. O tempo total e os erros de sequência são úteis para comparar velocidade de processamento, alternância cognitiva e fadiga em acompanhamentos sucessivos."
    eyebrow="Trail Making Test - Parte B"
    accent="violet"
    @back="router.push('/testes')"
    @dashboard="router.push('/testes')"
  >
    <section class="grid gap-6 lg:grid-cols-[1.35fr_0.65fr]">
      <div class="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 text-slate-950 shadow-sm">
        <template v-if="phase === 'ready'">
          <div class="space-y-5">
            <p class="text-lg text-slate-700 leading-relaxed">Conecte os itens alternando números e letras em ordem crescente. Exemplo: <strong>1 → A → 2 → B → 3 → C</strong>.</p>
            <div class="grid sm:grid-cols-3 gap-4">
              <div class="rounded-2xl bg-slate-100 p-4 border border-slate-200"><p class="text-sm font-bold text-slate-500">Itens</p><p class="text-2xl font-black">{{ trailSequence.length }}</p></div>
              <div class="rounded-2xl bg-slate-100 p-4 border border-slate-200"><p class="text-sm font-bold text-slate-500">Métrica</p><p class="text-2xl font-black">Tempo + erro</p></div>
              <div class="rounded-2xl bg-slate-100 p-4 border border-slate-200"><p class="text-sm font-bold text-slate-500">Uso clínico</p><p class="text-2xl font-black">Atenção executiva</p></div>
            </div>
            <button @click="startTest" class="rounded-2xl bg-violet-600 px-6 py-4 text-xl font-black text-white hover:bg-violet-500">Iniciar teste</button>
          </div>
        </template>

        <template v-else-if="phase === 'running'">
          <div class="space-y-6">
            <div class="flex items-center justify-between gap-3">
              <p class="text-sm font-black uppercase tracking-[0.2em] text-slate-500">Progresso</p>
              <p class="text-sm font-black uppercase tracking-[0.2em] text-slate-500">Próximo: {{ expectedToken?.label }}</p>
            </div>

            <div class="h-4 rounded-full bg-slate-100 overflow-hidden border border-slate-200">
              <div class="h-full bg-violet-600 transition-all" :style="{ width: `${completionPercent}%` }"></div>
            </div>

            <div class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-3">
              <button
                v-for="item in board"
                :key="item.id"
                @click="handleClick(item)"
                class="rounded-3xl border-2 bg-white px-4 py-8 text-center transition-all hover:-translate-y-0.5"
                :class="item.id === expectedToken?.id ? 'border-violet-500 bg-violet-50' : 'border-slate-200 hover:border-slate-300'"
              >
                <p class="text-4xl font-black text-slate-950">{{ item.label }}</p>
              </button>
            </div>

            <div class="rounded-2xl border border-violet-200 bg-violet-50 p-4 text-lg font-semibold text-violet-900">
              Clique no próximo item da sequência sem alterar a ordem.
            </div>
          </div>
        </template>

        <template v-else>
          <div class="space-y-6">
            <div class="rounded-3xl border border-slate-200 bg-slate-50 p-6">
              <p class="text-sm font-black uppercase tracking-[0.2em] text-slate-500">Resultado</p>
              <h2 class="text-3xl font-black text-slate-950 mt-2">JSON exportado com sequência e erros</h2>
              <p class="text-slate-600 mt-3">A análise longitudinal de tempo total e erros de sequência ajuda a rastrear alternância cognitiva, flexibilidade mental e processamento visuomotor.</p>
            </div>

            <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div class="rounded-2xl border border-slate-200 p-4"><p class="text-sm font-bold text-slate-500">Tempo total</p><p class="text-3xl font-black text-slate-950">{{ currentExport?.summary?.completionTimeMs || 0 }} ms</p></div>
              <div class="rounded-2xl border border-slate-200 p-4"><p class="text-sm font-bold text-slate-500">Erros</p><p class="text-3xl font-black text-slate-950">{{ errorCount }}</p></div>
              <div class="rounded-2xl border border-slate-200 p-4"><p class="text-sm font-bold text-slate-500">Passos corretos</p><p class="text-3xl font-black text-slate-950">{{ trailSequence.length - errorCount }}</p></div>
              <div class="rounded-2xl border border-slate-200 p-4"><p class="text-sm font-bold text-slate-500">Cliques</p><p class="text-3xl font-black text-slate-950">{{ clickCount }}</p></div>
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
            <div class="rounded-2xl bg-slate-800 p-4"><p class="text-xs uppercase tracking-[0.2em] text-slate-400">Erros</p><p class="text-3xl font-black">{{ errorCount }}</p></div>
            <div class="rounded-2xl bg-slate-800 p-4"><p class="text-xs uppercase tracking-[0.2em] text-slate-400">Esperado</p><p class="text-3xl font-black">{{ expectedToken?.label || '—' }}</p></div>
          </div>
          <div class="mt-3 rounded-2xl bg-violet-500/15 p-4 text-violet-50">
            <p class="text-xs uppercase tracking-[0.2em] text-violet-200">Comentário longitudinal</p>
            <p class="mt-2 text-sm leading-relaxed">A redução do tempo total com manutenção ou redução de erros ao longo do seguimento sugere melhora; aumento de erros com lentificação pode indicar declínio executivo.</p>
          </div>
        </div>

        <div class="rounded-3xl border border-slate-200 bg-white p-5 text-slate-950 shadow-sm max-h-[520px] overflow-auto">
          <p class="text-sm font-black uppercase tracking-[0.2em] text-slate-500">Logs de clique</p>
          <div class="mt-4 space-y-3">
            <div v-for="entry in store.state.clickLogs" :key="entry.id" class="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm">
              <p class="font-bold">{{ entry.itemLabel }}</p>
              <p class="text-slate-600">{{ entry.correct ? 'Sequência correta' : 'Erro de sequência' }}</p>
            </div>
          </div>
        </div>
      </aside>
    </section>
  </DiagnosticShell>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import DiagnosticShell from '../components/diagnostics/DiagnosticShell.vue'
import { diagnosticRoutes, semanticCategories, shuffleArray } from '../data/diagnosticTests'
import { useDiagnosticTestStore } from '../stores/diagnosticTestStore'
import { getCurrentUserProfile } from '../services/sessionUser'
import { salvarResultadoTeste } from '../services/testResults'
import { downloadJson } from '../utils/downloadJson'

const router = useRouter()
const store = useDiagnosticTestStore()

const testId = 'fluencia-semantica'
const testName = 'Teste de Fluência Semântica'
const testType = 'fluencia-semantica'
const durationSeconds = 60

const selectedCategoryId = ref('animais')
const phase = ref('ready')
const remainingSeconds = ref(durationSeconds)
const selectionCounts = ref({})
const totalCorrect = ref(0)
const totalPerseverations = ref(0)
const totalIntrusions = ref(0)
const clickCount = ref(0)
const sessionStartedAtMs = ref(0)
const currentExport = ref(null)
let intervalId = null

const selectedCategory = computed(() => semanticCategories[selectedCategoryId.value])
const items = computed(() => shuffleArray([...selectedCategory.value.correct, ...selectedCategory.value.distractors]))
const uniqueSelectedIds = computed(() => Object.keys(selectionCounts.value))
const progressPercent = computed(() => Math.round(((durationSeconds - remainingSeconds.value) / durationSeconds) * 100))

const startTest = () => {
  store.startSession({
    testId,
    testName,
    testType,
    userProfile: getCurrentUserProfile(),
    metadata: {
      categoryId: selectedCategoryId.value,
      categoryLabel: selectedCategory.value.label,
      durationSeconds,
    },
  })

  selectionCounts.value = {}
  totalCorrect.value = 0
  totalPerseverations.value = 0
  totalIntrusions.value = 0
  clickCount.value = 0
  currentExport.value = null
  remainingSeconds.value = durationSeconds
  sessionStartedAtMs.value = Date.now()
  phase.value = 'running'

  clearInterval(intervalId)
  intervalId = setInterval(() => {
    remainingSeconds.value -= 1
    if (remainingSeconds.value <= 0) {
      finishTest()
    }
  }, 1000)
}

const handlePick = (item) => {
  if (phase.value !== 'running') {
    return
  }

  clickCount.value += 1
  const repeated = Boolean(selectionCounts.value[item.id])
  const isCorrectCategory = selectedCategory.value.correct.some((stimulus) => stimulus.id === item.id)

  selectionCounts.value[item.id] = (selectionCounts.value[item.id] || 0) + 1

  if (isCorrectCategory && !repeated) {
    totalCorrect.value += 1
  } else if (isCorrectCategory && repeated) {
    totalPerseverations.value += 1
  } else if (!isCorrectCategory) {
    totalIntrusions.value += 1
  }

  store.logClick({
    testId,
    testName,
    testType,
    categoryId: selectedCategory.value.id,
    itemId: item.id,
    itemLabel: item.label,
    correct: isCorrectCategory && !repeated,
    repeated,
    intrusion: !isCorrectCategory,
    latencyMs: Date.now() - sessionStartedAtMs.value,
    totalClicks: clickCount.value,
  })

  store.logResponse({
    testId,
    testName,
    testType,
    categoryId: selectedCategory.value.id,
    itemId: item.id,
    itemLabel: item.label,
    correct: isCorrectCategory && !repeated,
    repeated,
    intrusion: !isCorrectCategory,
    latencyMs: Date.now() - sessionStartedAtMs.value,
    totalClicks: clickCount.value,
  })
}

const finishTest = async () => {
  clearInterval(intervalId)
  phase.value = 'result'

  const summary = {
    totalClicks: clickCount.value,
    totalCorrect: totalCorrect.value,
    totalPerseverations: totalPerseverations.value,
    totalIntrusions: totalIntrusions.value,
    accuracyPercent: clickCount.value ? Math.round((totalCorrect.value / clickCount.value) * 100) : 0,
    categoryId: selectedCategory.value.id,
    categoryLabel: selectedCategory.value.label,
    durationSeconds,
  }

  const exportPayload = store.finishSession(summary, {
    selectedCategory: selectedCategory.value,
    selectedIds: [...uniqueSelectedIds.value],
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
      selectedCategory: selectedCategory.value,
      selectedIds: [...uniqueSelectedIds.value],
      selectionCounts: { ...selectionCounts.value },
    },
    userProfile: getCurrentUserProfile(),
  })
}

const downloadCurrentJson = () => {
  if (!currentExport.value) return
  downloadJson('mente-ativa-fluencia-semantica.json', currentExport.value)
}

const restart = () => {
  store.reset()
  selectionCounts.value = {}
  totalCorrect.value = 0
  totalPerseverations.value = 0
  totalIntrusions.value = 0
  clickCount.value = 0
  currentExport.value = null
  remainingSeconds.value = durationSeconds
  phase.value = 'ready'
}

onBeforeUnmount(() => {
  clearInterval(intervalId)
})
</script>

<template>
  <DiagnosticShell
    title="Teste de Fluência Semântica"
    subtitle="O paciente deve selecionar o maior número possível de itens pertencentes à categoria escolhida dentro de 60 segundos. Repetições e intrusões são armazenadas no JSON para apoiar análise longitudinal do comprometimento executivo e da fluência verbal."
    eyebrow="Categorização semântica"
    accent="amber"
    @back="router.push('/testes')"
    @dashboard="router.push('/testes')"
  >
    <section class="grid gap-6 lg:grid-cols-[1.35fr_0.65fr]">
      <div class="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 text-slate-950 shadow-sm">
        <template v-if="phase === 'ready'">
          <div class="space-y-5">
            <p class="text-lg text-slate-700 leading-relaxed">Escolha uma categoria e toque nos itens correspondentes. Repetir o mesmo item conta como <strong>perseveração</strong>, enquanto itens de fora da categoria contam como <strong>intrusões</strong>.</p>

            <div class="grid sm:grid-cols-2 gap-4">
              <button
                v-for="category in Object.values(semanticCategories)"
                :key="category.id"
                @click="selectedCategoryId = category.id"
                class="rounded-3xl border-2 p-5 text-left transition-all"
                :class="selectedCategoryId === category.id ? 'border-amber-500 bg-amber-50' : 'border-slate-200 bg-slate-50 hover:bg-slate-100'"
              >
                <p class="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Categoria</p>
                <p class="mt-1 text-2xl font-black">{{ category.label }}</p>
                <p class="mt-2 text-slate-600">{{ category.description }}</p>
              </button>
            </div>

            <button @click="startTest" class="rounded-2xl bg-amber-500 px-6 py-4 text-xl font-black text-slate-950 hover:bg-amber-400">Iniciar 60 segundos</button>
          </div>
        </template>

        <template v-else-if="phase === 'running'">
          <div class="space-y-6">
            <div class="flex items-center justify-between gap-3">
              <p class="text-sm font-black uppercase tracking-[0.2em] text-slate-500">Tempo restante</p>
              <p class="text-sm font-black uppercase tracking-[0.2em] text-slate-500">{{ progressPercent }}%</p>
            </div>

            <div class="h-4 rounded-full bg-slate-100 overflow-hidden border border-slate-200">
              <div class="h-full bg-amber-500 transition-all" :style="{ width: `${progressPercent}%` }"></div>
            </div>

            <div class="rounded-3xl border-4 border-slate-200 bg-slate-950 p-6 text-center shadow-lg">
              <p class="text-6xl sm:text-7xl">{{ selectedCategory.label.includes('Animais') ? '🐾' : '🍳' }}</p>
              <p class="text-2xl sm:text-3xl font-black text-white mt-3">{{ remainingSeconds }} segundos</p>
              <p class="text-slate-300 mt-2">{{ selectedCategory.description }}</p>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              <button
                v-for="item in items"
                :key="item.id"
                @click="handlePick(item)"
                class="rounded-3xl border-2 bg-white p-4 text-left transition-all hover:-translate-y-0.5"
                :class="selectionCounts[item.id] ? 'border-amber-500 bg-amber-50' : 'border-slate-200 hover:border-slate-300'"
              >
                <p class="text-3xl">{{ item.icon }}</p>
                <p class="mt-2 text-lg font-black text-slate-950">{{ item.label }}</p>
                <p class="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">Toque múltiplo permitido</p>
              </button>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="space-y-6">
            <div class="rounded-3xl border border-slate-200 bg-slate-50 p-6">
              <p class="text-sm font-black uppercase tracking-[0.2em] text-slate-500">Resultado</p>
              <h2 class="text-3xl font-black text-slate-950 mt-2">JSON exportado com fluência semântica</h2>
              <p class="text-slate-600 mt-3">Os logs de seleção identificam perseveração e intrusões, úteis para comparar mudanças em controle inibitório e recuperação lexical em avaliações sucessivas.</p>
            </div>

            <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div class="rounded-2xl border border-slate-200 p-4"><p class="text-sm font-bold text-slate-500">Acertos</p><p class="text-3xl font-black text-slate-950">{{ totalCorrect }}</p></div>
              <div class="rounded-2xl border border-slate-200 p-4"><p class="text-sm font-bold text-slate-500">Perseveração</p><p class="text-3xl font-black text-slate-950">{{ totalPerseverations }}</p></div>
              <div class="rounded-2xl border border-slate-200 p-4"><p class="text-sm font-bold text-slate-500">Intrusões</p><p class="text-3xl font-black text-slate-950">{{ totalIntrusions }}</p></div>
              <div class="rounded-2xl border border-slate-200 p-4"><p class="text-sm font-bold text-slate-500">Precisão</p><p class="text-3xl font-black text-slate-950">{{ clickCount ? Math.round((totalCorrect / clickCount) * 100) : 0 }}%</p></div>
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
            <div class="rounded-2xl bg-slate-800 p-4"><p class="text-xs uppercase tracking-[0.2em] text-slate-400">Toques</p><p class="text-3xl font-black">{{ clickCount }}</p></div>
            <div class="rounded-2xl bg-slate-800 p-4"><p class="text-xs uppercase tracking-[0.2em] text-slate-400">Restante</p><p class="text-3xl font-black">{{ remainingSeconds }}s</p></div>
          </div>
          <div class="mt-3 rounded-2xl bg-amber-500/15 p-4 text-amber-50">
            <p class="text-xs uppercase tracking-[0.2em] text-amber-200">Comentário longitudinal</p>
            <p class="mt-2 text-sm leading-relaxed">A evolução de perseverações e intrusões ao longo das sessões ajuda a rastrear desorganização executiva e enfraquecimento do controle semântico.</p>
          </div>
        </div>

        <div class="rounded-3xl border border-slate-200 bg-white p-5 text-slate-950 shadow-sm max-h-[520px] overflow-auto">
          <p class="text-sm font-black uppercase tracking-[0.2em] text-slate-500">Logs de clique</p>
          <div class="mt-4 space-y-3">
            <div v-for="entry in store.state.clickLogs" :key="entry.id" class="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm">
              <p class="font-bold">{{ entry.itemLabel }}</p>
              <p class="text-slate-600">{{ entry.correct ? 'Acerto' : entry.repeated ? 'Repetição' : 'Intrusão' }}</p>
            </div>
          </div>
        </div>
      </aside>
    </section>
  </DiagnosticShell>
</template>

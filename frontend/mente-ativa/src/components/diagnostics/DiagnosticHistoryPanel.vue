<script setup>
defineProps({
  records: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['download-json', 'rerun'])

const metricLabelMap = {
  'n-back-2': ['Precisão', 'Latência média'],
  'fluencia-semantica': ['Acertos', 'Intrusões', 'Perseveração'],
  'trail-b': ['Tempo total', 'Erros de sequência'],
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

const summaryText = (record) => {
  const summary = record?.summary || {}
  if (record.testType === 'n-back-2') {
    return `${summary.accuracyPercent ?? 0}% | ${summary.averageLatencyMs ?? 0} ms`
  }
  if (record.testType === 'fluencia-semantica') {
    return `${summary.totalCorrect ?? 0} acertos | ${summary.totalIntrusions ?? 0} intrusões`
  }
  return `${summary.completionTimeMs ?? 0} ms | ${summary.errorCount ?? 0} erros`
}
</script>

<template>
  <section class="bg-white border border-slate-200 rounded-3xl shadow-sm overflow-hidden">
    <div class="p-6 sm:p-8 border-b border-slate-200 bg-slate-50">
      <h2 class="text-2xl font-black text-slate-900">Histórico de Testes</h2>
      <p class="text-slate-600 mt-2">Cada resultado guarda métricas e o log dos cliques para acompanhar a evolução longitudinal do paciente ao longo do tempo.</p>
    </div>

    <div v-if="!records.length" class="p-8 text-center space-y-3">
      <p class="text-5xl">📋</p>
      <p class="text-xl font-bold text-slate-900">Nenhum teste registrado</p>
      <p class="text-slate-600">Realize um dos testes para gerar o histórico e exportação JSON.</p>
    </div>

    <div v-else class="divide-y divide-slate-200">
      <article v-for="record in records" :key="record.id" class="p-6 sm:p-8 space-y-5">
        <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div class="space-y-2">
            <div class="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-black uppercase tracking-[0.2em] text-emerald-700">
              {{ record.testTypeLabel || record.testType || record.testId }}
            </div>
            <h3 class="text-2xl font-black text-slate-900">{{ record.testName }}</h3>
            <p class="text-slate-600">{{ formatDate(record.createdAtMs) }}</p>
          </div>

          <div class="flex flex-wrap gap-3">
            <button
              @click="$emit('download-json', record)"
              class="rounded-2xl bg-slate-900 px-5 py-3 font-bold text-white hover:bg-slate-800"
            >
              Baixar JSON
            </button>
            <button
              @click="$emit('rerun', record)"
              class="rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-3 font-bold text-emerald-700 hover:bg-emerald-100"
            >
              Repetir teste
            </button>
          </div>
        </div>

        <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-500">Resumo</p>
            <p class="text-lg font-black text-slate-900 mt-2">{{ summaryText(record) }}</p>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-500">Clicks logados</p>
            <p class="text-lg font-black text-slate-900 mt-2">{{ record.clickLogs?.length || 0 }}</p>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-500">Respostas</p>
            <p class="text-lg font-black text-slate-900 mt-2">{{ record.responseLogs?.length || 0 }}</p>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-500">Métricas-chave</p>
            <p class="text-lg font-black text-slate-900 mt-2">{{ metricLabelMap[record.testType]?.join(' • ') || 'Dados estruturados' }}</p>
          </div>
        </div>

        <div class="overflow-x-auto rounded-2xl border border-slate-200">
          <table class="w-full text-sm">
            <thead class="bg-slate-100 text-left text-slate-700">
              <tr>
                <th class="px-4 py-3">Métrica</th>
                <th class="px-4 py-3">Valor</th>
              </tr>
            </thead>
            <tbody>
              <tr class="border-t border-slate-200">
                <td class="px-4 py-3 font-semibold">Precisão / Acertos</td>
                <td class="px-4 py-3">{{ record.summary?.accuracyPercent ?? record.summary?.totalCorrect ?? record.summary?.correctResponses ?? 0 }}</td>
              </tr>
              <tr class="border-t border-slate-200">
                <td class="px-4 py-3 font-semibold">Latência / Tempo</td>
                <td class="px-4 py-3">{{ record.summary?.averageLatencyMs ?? record.summary?.completionTimeMs ?? record.summary?.averageResponseMs ?? 0 }} ms</td>
              </tr>
              <tr class="border-t border-slate-200">
                <td class="px-4 py-3 font-semibold">Erros / Intrusões</td>
                <td class="px-4 py-3">{{ record.summary?.errorCount ?? record.summary?.totalIntrusions ?? record.summary?.incorrectResponses ?? 0 }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>
    </div>
  </section>
</template>

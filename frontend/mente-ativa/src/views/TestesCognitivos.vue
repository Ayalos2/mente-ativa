<script setup>
import { useRouter } from 'vue-router'
import DiagnosticShell from '../components/diagnostics/DiagnosticShell.vue'
import { diagnosticRoutes, semanticCategories } from '../data/diagnosticTests'

const router = useRouter()

const cards = [
  {
    title: 'Memória de Curto Prazo',
    route: diagnosticRoutes.nback,
    accent: 'emerald',
    label: 'N-Back Adaptado',
    description: 'Identifica se o item atual é igual ao de dois turnos atrás. Útil para medir precisão e latência de resposta.',
    metrics: ['Precisão', 'Latência por resposta', 'Resposta correta/erro'],
  },
  {
    title: 'Fluência Semântica',
    route: diagnosticRoutes.fluency,
    accent: 'amber',
    label: semanticCategories.animais.label,
    description: 'Seleção de itens por categoria para rastrear perseveração e intrusões em janela de 60 segundos.',
    metrics: ['Acertos', 'Perseveração', 'Intrusões'],
  },
  {
    title: 'Atenção Alternada',
    route: diagnosticRoutes.trail,
    accent: 'violet',
    label: 'Trail Making Test B',
    description: 'Conexão alternada entre números e letras em sequência crescente. Mede tempo total e erros de sequência.',
    metrics: ['Tempo total', 'Erros de sequência', 'Click log'],
  },
]
</script>

<template>
  <DiagnosticShell
    title="Painel Diagnóstico Cognitivo"
    subtitle="Escolha um dos três testes para monitorar desempenho cognitivo ao longo do tempo. Cada sessão gera um JSON estruturado com clique, latência e resumo clínico para acompanhar possíveis sinais de declínio longitudinal."
    eyebrow="HealthTech / Alzheimer"
    accent="emerald"
    @back="router.push('/profile')"
    @dashboard="router.push('/profile')"
  >
    <section class="grid gap-6 lg:grid-cols-3">
      <article
        v-for="card in cards"
        :key="card.title"
        class="rounded-3xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm flex flex-col gap-4"
      >
        <div class="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-black uppercase tracking-[0.2em] text-slate-700 w-fit">
          {{ card.label }}
        </div>

        <div class="space-y-2">
          <h2 class="text-2xl font-black text-slate-950">{{ card.title }}</h2>
          <p class="text-slate-600 leading-relaxed">{{ card.description }}</p>
        </div>

        <div class="flex flex-wrap gap-2">
          <span v-for="metric in card.metrics" :key="metric" class="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-700">{{ metric }}</span>
        </div>

        <button
          @click="router.push(card.route)"
          class="mt-auto rounded-2xl bg-slate-950 px-5 py-3 font-black text-white hover:bg-slate-800"
        >
          Iniciar teste
        </button>
      </article>
    </section>
  </DiagnosticShell>
</template>

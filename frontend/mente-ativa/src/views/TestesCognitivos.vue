<script setup>
import { useRouter } from 'vue-router'
import DiagnosticShell from '../components/diagnostics/DiagnosticShell.vue'
import TestCard from '../components/diagnostics/TestCard.vue'
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

const handleStartTest = (route) => {
  router.push(route)
}
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
      <TestCard
        v-for="card in cards"
        :key="card.title"
        :title="card.title"
        :label="card.label"
        :description="card.description"
        :metrics="card.metrics"
        :route="card.route"
        :accent="card.accent"
        @start="handleStartTest(card.route)"
      />
    </section>
  </DiagnosticShell>
</template>

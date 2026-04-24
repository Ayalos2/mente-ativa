<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const bancoPalavras = [
  'Casa', 'Floresta', 'Cadeira', 'Laranja', 'Computador', 'Janela',
  'Relogio', 'Ponte', 'Livro', 'Nuvem', 'Telefone', 'Chave',
  'Caneta', 'Abacaxi', 'Violao', 'Hospital', 'Martelo', 'Sapato'
]

const tempoEstudoSegundos = 12
const totalPerguntas = 8

const etapa = ref('pronto')
const palavrasParaMemorizar = ref([])
const perguntas = ref([])
const indicePergunta = ref(0)
const respostas = ref([])
const tempoRestante = ref(tempoEstudoSegundos)
let timerId = null

const perguntaAtual = computed(() => perguntas.value[indicePergunta.value] || null)
const acertos = computed(() => respostas.value.filter((r) => r.correta).length)
const percentual = computed(() => {
  if (!respostas.value.length) return 0
  return Math.round((acertos.value / respostas.value.length) * 100)
})

const mensagemFinal = computed(() => {
  if (percentual.value >= 85) return 'Excelente memoria de curto prazo.'
  if (percentual.value >= 60) return 'Bom desempenho. Ha pequenas oportunidades de melhoria.'
  return 'Desempenho abaixo do esperado. Recomenda-se repetir o teste em outro momento.'
})

const embaralhar = (lista) => {
  const copia = [...lista]
  for (let i = copia.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    const tmp = copia[i]
    copia[i] = copia[j]
    copia[j] = tmp
  }
  return copia
}

const gerarRodada = () => {
  const embaralhada = embaralhar(bancoPalavras)
  palavrasParaMemorizar.value = embaralhada.slice(0, 8)

  const presentes = embaralhar(palavrasParaMemorizar.value).slice(0, 4)
  const ausentes = embaralhar(
    bancoPalavras.filter((p) => !palavrasParaMemorizar.value.includes(p))
  ).slice(0, 4)

  perguntas.value = embaralhar([
    ...presentes.map((palavra) => ({ palavra, estavaNaLista: true })),
    ...ausentes.map((palavra) => ({ palavra, estavaNaLista: false }))
  ]).slice(0, totalPerguntas)

  indicePergunta.value = 0
  respostas.value = []
}

const iniciarTeste = () => {
  gerarRodada()
  etapa.value = 'memorizar'
  tempoRestante.value = tempoEstudoSegundos

  clearInterval(timerId)
  timerId = setInterval(() => {
    tempoRestante.value -= 1
    if (tempoRestante.value <= 0) {
      clearInterval(timerId)
      etapa.value = 'perguntas'
    }
  }, 1000)
}

const responder = (respostaUsuario) => {
  const atual = perguntaAtual.value
  if (!atual) return

  const correta = respostaUsuario === atual.estavaNaLista
  respostas.value.push({
    palavra: atual.palavra,
    respostaUsuario,
    correta,
    respostaCorreta: atual.estavaNaLista,
  })

  if (indicePergunta.value >= perguntas.value.length - 1) {
    etapa.value = 'resultado'
    return
  }

  indicePergunta.value += 1
}

const reiniciar = () => {
  clearInterval(timerId)
  etapa.value = 'pronto'
  palavrasParaMemorizar.value = []
  perguntas.value = []
  respostas.value = []
  indicePergunta.value = 0
}
</script>

<template>
  <div class="min-h-screen bg-slate-100 text-slate-900">
    <header class="bg-white border-b border-slate-200">
      <div class="max-w-5xl mx-auto px-4 sm:px-6 py-5 flex items-center justify-between">
        <div>
          <p class="text-xs font-semibold tracking-[0.2em] uppercase text-emerald-600">Modulo protegido</p>
          <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight">Teste de Memoria</h1>
        </div>
        <button
          @click="router.push('/profile')"
          class="px-4 py-2 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 font-semibold"
        >
          Voltar ao Perfil
        </button>
      </div>
    </header>

    <main class="max-w-5xl mx-auto px-4 sm:px-6 py-10">
      <div class="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 sm:p-8">

        <section v-if="etapa === 'pronto'" class="space-y-6">
          <h2 class="text-2xl font-bold">Como funciona</h2>
          <p class="text-slate-600 leading-relaxed">
            Voce vera uma lista com 8 palavras durante alguns segundos. Em seguida,
            respondera se cada palavra apareceu ou nao na lista original.
          </p>

          <div class="grid sm:grid-cols-3 gap-4">
            <div class="rounded-xl bg-blue-50 border border-blue-100 p-4">
              <p class="text-sm text-blue-700 font-semibold">Tempo de estudo</p>
              <p class="text-2xl font-extrabold text-blue-900">{{ tempoEstudoSegundos }}s</p>
            </div>
            <div class="rounded-xl bg-emerald-50 border border-emerald-100 p-4">
              <p class="text-sm text-emerald-700 font-semibold">Perguntas</p>
              <p class="text-2xl font-extrabold text-emerald-900">{{ totalPerguntas }}</p>
            </div>
            <div class="rounded-xl bg-amber-50 border border-amber-100 p-4">
              <p class="text-sm text-amber-700 font-semibold">Objetivo</p>
              <p class="text-2xl font-extrabold text-amber-900">Lembranca</p>
            </div>
          </div>

          <button
            @click="iniciarTeste"
            class="w-full sm:w-auto px-8 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold"
          >
            Iniciar rodada
          </button>
        </section>

        <section v-else-if="etapa === 'memorizar'" class="space-y-6">
          <div class="flex items-center justify-between gap-4">
            <h2 class="text-2xl font-bold">Memorize as palavras</h2>
            <div class="px-4 py-2 rounded-full bg-emerald-100 text-emerald-800 font-bold">
              {{ tempoRestante }}s
            </div>
          </div>

          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div
              v-for="palavra in palavrasParaMemorizar"
              :key="palavra"
              class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-4 text-center font-semibold"
            >
              {{ palavra }}
            </div>
          </div>
        </section>

        <section v-else-if="etapa === 'perguntas' && perguntaAtual" class="space-y-6">
          <div class="flex items-center justify-between">
            <p class="text-sm font-semibold text-slate-600 uppercase tracking-wide">
              Pergunta {{ indicePergunta + 1 }} de {{ perguntas.length }}
            </p>
            <p class="text-sm font-semibold text-emerald-700">
              Acertos: {{ acertos }}
            </p>
          </div>

          <div class="rounded-2xl border border-slate-200 p-6 bg-slate-50">
            <p class="text-lg sm:text-xl font-medium">A palavra abaixo estava na lista inicial?</p>
            <p class="text-4xl font-extrabold mt-4 tracking-tight">{{ perguntaAtual.palavra }}</p>
          </div>

          <div class="flex flex-col sm:flex-row gap-3">
            <button
              @click="responder(true)"
              class="flex-1 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold"
            >
              Sim, estava
            </button>
            <button
              @click="responder(false)"
              class="flex-1 px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-900 text-white font-bold"
            >
              Nao estava
            </button>
          </div>
        </section>

        <section v-else-if="etapa === 'resultado'" class="space-y-6">
          <h2 class="text-2xl font-bold">Resultado da rodada</h2>

          <div class="rounded-2xl p-6 bg-emerald-50 border border-emerald-100">
            <p class="text-sm font-semibold uppercase tracking-wide text-emerald-700">Pontuacao</p>
            <p class="text-4xl font-extrabold text-emerald-900 mt-2">{{ acertos }} / {{ respostas.length }}</p>
            <p class="text-emerald-800 font-medium mt-2">{{ percentual }}% de acerto</p>
            <p class="text-slate-700 mt-3">{{ mensagemFinal }}</p>
          </div>

          <div class="overflow-x-auto rounded-xl border border-slate-200">
            <table class="w-full text-sm">
              <thead class="bg-slate-100 text-left">
                <tr>
                  <th class="px-4 py-3">Palavra</th>
                  <th class="px-4 py-3">Sua resposta</th>
                  <th class="px-4 py-3">Correta</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in respostas" :key="item.palavra" class="border-t border-slate-200">
                  <td class="px-4 py-3 font-medium">{{ item.palavra }}</td>
                  <td class="px-4 py-3">{{ item.respostaUsuario ? 'Estava' : 'Nao estava' }}</td>
                  <td class="px-4 py-3" :class="item.correta ? 'text-emerald-700 font-semibold' : 'text-red-700 font-semibold'">
                    {{ item.respostaCorreta ? 'Estava' : 'Nao estava' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="flex flex-col sm:flex-row gap-3">
            <button
              @click="iniciarTeste"
              class="px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold"
            >
              Fazer nova rodada
            </button>
            <button
              @click="reiniciar"
              class="px-6 py-3 rounded-xl bg-slate-200 hover:bg-slate-300 text-slate-900 font-bold"
            >
              Voltar ao inicio
            </button>
          </div>
        </section>

      </div>
    </main>
  </div>
</template>

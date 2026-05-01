import { computed, onBeforeUnmount, ref } from 'vue'
import { salvarResultadoTeste } from '../services/testResults'
import { getCurrentUserProfile } from '../services/sessionUser'

const embaralhar = (lista) => {
  const copia = [...lista]

  for (let indice = copia.length - 1; indice > 0; indice -= 1) {
    const aleatorio = Math.floor(Math.random() * (indice + 1))
    const temporario = copia[indice]
    copia[indice] = copia[aleatorio]
    copia[aleatorio] = temporario
  }

  return copia
}

export function useRecognitionTest({
  testId,
  testName,
  wordBank,
  studySeconds,
  totalQuestions,
  memorizationCount,
  positiveQuestionsCount,
  successMessage,
  mediumMessage,
  lowMessage,
}) {
  const etapa = ref('pronto')
  const palavrasParaMemorizar = ref([])
  const perguntas = ref([])
  const indicePergunta = ref(0)
  const respostas = ref([])
  const tempoRestante = ref(studySeconds)
  const salvandoResultado = ref(false)
  const resultadoSalvo = ref(false)
  const inicioRodadaMs = ref(0)
  const inicioPerguntaMs = ref(0)

  let timerId = null

  const perguntaAtual = computed(() => perguntas.value[indicePergunta.value] || null)
  const acertos = computed(() => respostas.value.filter((resposta) => resposta.correta).length)
  const erros = computed(() => respostas.value.filter((resposta) => !resposta.correta).length)
  const percentual = computed(() => {
    if (!respostas.value.length) {
      return 0
    }

    return Math.round((acertos.value / respostas.value.length) * 100)
  })
  const tempoTotalRespostaMs = computed(() => {
    return respostas.value.reduce((acumulado, resposta) => acumulado + resposta.tempoRespostaMs, 0)
  })
  const tempoRespostaMediaMs = computed(() => {
    if (!respostas.value.length) {
      return 0
    }

    return Math.round(tempoTotalRespostaMs.value / respostas.value.length)
  })
  const tempoOciosoMs = computed(() => studySeconds * 1000)
  const tempoTotalTesteMs = computed(() => {
    if (!inicioRodadaMs.value) {
      return 0
    }

    return Date.now() - inicioRodadaMs.value
  })
  const mensagemFinal = computed(() => {
    if (percentual.value >= 85) {
      return successMessage
    }

    if (percentual.value >= 60) {
      return mediumMessage
    }

    return lowMessage
  })

  const limparTimer = () => {
    if (timerId) {
      clearInterval(timerId)
      timerId = null
    }
  }

  const gerarRodada = () => {
    const palavrasEmbaralhadas = embaralhar(wordBank)
    palavrasParaMemorizar.value = palavrasEmbaralhadas.slice(0, memorizationCount)

    const perguntasPositivas = embaralhar(palavrasParaMemorizar.value).slice(0, positiveQuestionsCount)
    const perguntasNegativas = embaralhar(
      wordBank.filter((palavra) => !palavrasParaMemorizar.value.includes(palavra))
    ).slice(0, totalQuestions - positiveQuestionsCount)

    perguntas.value = embaralhar([
      ...perguntasPositivas.map((palavra) => ({ palavra, estavaNaLista: true })),
      ...perguntasNegativas.map((palavra) => ({ palavra, estavaNaLista: false })),
    ]).slice(0, totalQuestions)

    indicePergunta.value = 0
    respostas.value = []
    resultadoSalvo.value = false
  }

  const salvarResultado = async () => {
    if (resultadoSalvo.value) {
      return
    }

    salvandoResultado.value = true

    try {
      await salvarResultadoTeste({
        testId,
        testName,
        summary: {
          totalQuestions: respostas.value.length,
          correctAnswers: acertos.value,
          wrongAnswers: erros.value,
          accuracyPercent: percentual.value,
          averageResponseMs: tempoRespostaMediaMs.value,
          totalResponseMs: tempoTotalRespostaMs.value,
          totalIdleMs: tempoOciosoMs.value,
          memorizationMs: studySeconds * 1000,
          durationMs: tempoTotalTesteMs.value,
        },
        questionResults: respostas.value,
        userProfile: getCurrentUserProfile(),
      })
      resultadoSalvo.value = true
    } catch (error) {
      console.error('Nao foi possivel salvar o resultado do teste no Firebase:', error)
    } finally {
      salvandoResultado.value = false
    }
  }

  const concluirRodada = async () => {
    etapa.value = 'resultado'
    await salvarResultado()
  }

  const iniciarPerguntas = () => {
    limparTimer()
    etapa.value = 'perguntas'
    inicioPerguntaMs.value = Date.now()
  }

  const iniciarTeste = () => {
    gerarRodada()
    etapa.value = 'memorizar'
    tempoRestante.value = studySeconds
    inicioRodadaMs.value = Date.now()

    limparTimer()
    timerId = setInterval(() => {
      tempoRestante.value -= 1

      if (tempoRestante.value <= 0) {
        iniciarPerguntas()
      }
    }, 1000)
  }

  const responder = async (respostaUsuario) => {
    const pergunta = perguntaAtual.value

    if (!pergunta) {
      return
    }

    const tempoRespostaMs = Math.max(Date.now() - inicioPerguntaMs.value, 0)
    const correta = respostaUsuario === pergunta.estavaNaLista

    respostas.value.push({
      palavra: pergunta.palavra,
      respostaUsuario,
      correta,
      respostaCorreta: pergunta.estavaNaLista,
      tempoRespostaMs,
    })

    if (indicePergunta.value >= perguntas.value.length - 1) {
      await concluirRodada()
      return
    }

    indicePergunta.value += 1
    inicioPerguntaMs.value = Date.now()
  }

  const reiniciar = () => {
    limparTimer()
    etapa.value = 'pronto'
    palavrasParaMemorizar.value = []
    perguntas.value = []
    respostas.value = []
    indicePergunta.value = 0
    tempoRestante.value = studySeconds
    resultadoSalvo.value = false
    inicioRodadaMs.value = 0
    inicioPerguntaMs.value = 0
  }

  onBeforeUnmount(() => {
    limparTimer()
  })

  return {
    etapa,
    palavrasParaMemorizar,
    perguntas,
    indicePergunta,
    respostas,
    tempoRestante,
    salvandoResultado,
    perguntaAtual,
    acertos,
    erros,
    percentual,
    tempoRespostaMediaMs,
    tempoOciosoMs,
    tempoTotalRespostaMs,
    tempoTotalTesteMs,
    mensagemFinal,
    iniciarTeste,
    responder,
    reiniciar,
  }
}
import { addDoc, collection, getDocs, query, where } from 'firebase/firestore'
import { db, isFirebaseConfigured } from '../config/firebase'
import { getCurrentUserProfile, getUserKey } from './sessionUser'

const COLLECTION_NAME = 'historico_testes'

const toNumber = (value) => {
  const numericValue = Number(value)
  return Number.isFinite(numericValue) ? numericValue : 0
}

export const salvarResultadoTeste = async ({
  testId,
  testName,
  testType,
  summary,
  clickLogs = [],
  responseLogs = [],
  exportPayload = null,
  structuredData = {},
  userProfile = getCurrentUserProfile(),
}) => {
  if (!isFirebaseConfigured || !db) {
    return null
  }

  const userKey = getUserKey(userProfile)

  if (!userKey) {
    return null
  }

  return addDoc(collection(db, COLLECTION_NAME), {
    userKey,
    userEmail: userProfile?.email || null,
    userName: userProfile?.nome || null,
    userPhoto: userProfile?.foto || null,
    testId,
    testName,
    testType: testType || testId,
    summary,
    clickLogs,
    responseLogs,
    structuredData,
    exportPayload,
    createdAtMs: Date.now(),
    createdAtIso: new Date().toISOString(),
  })
}

export const carregarHistoricoTestes = async ({ userProfile = getCurrentUserProfile() } = {}) => {
  if (!isFirebaseConfigured || !db) {
    return []
  }

  const userKey = getUserKey(userProfile)

  if (!userKey) {
    return []
  }

  const resultado = await getDocs(
    query(
      collection(db, COLLECTION_NAME),
      where('userKey', '==', userKey)
    )
  )

  return resultado.docs
    .map((documento) => ({
      id: documento.id,
      ...documento.data(),
    }))
    .sort((a, b) => toNumber(b.createdAtMs) - toNumber(a.createdAtMs))
}

export const formatarResultadoTeste = (registro) => {
  const summary = registro?.summary || {}

  return {
    ...registro,
    totalClicks: toNumber(summary.totalClicks),
    correctResponses: toNumber(summary.correctResponses),
    incorrectResponses: toNumber(summary.incorrectResponses),
    accuracyPercent: toNumber(summary.accuracyPercent),
    averageLatencyMs: toNumber(summary.averageLatencyMs),
    totalPerseverations: toNumber(summary.totalPerseverations),
    totalIntrusions: toNumber(summary.totalIntrusions),
    completionTimeMs: toNumber(summary.completionTimeMs),
    errorCount: toNumber(summary.errorCount),
    totalCorrect: toNumber(summary.totalCorrect),
    testTypeLabel: registro?.testType || registro?.testId || 'teste',
  }
}

const buildFeedbackMessages = ({ category, reasons = [], retestDays = null }) => {
  const shortByCategory = {
    normal: 'Resultados dentro do esperado. Reteste recomendado em 12 meses.',
    monitor: 'Leve alteração detectada. Acompanhe e repita em 3–6 meses.',
    procurar_medico: 'Alterações significativas detectadas — recomenda-se avaliação clínica.',
    urgencia: 'Alerta: procure atendimento médico imediato.',
  }

  const detailedByCategory = {
    normal: `Seu desempenho está dentro da faixa esperada para este teste. Motivos: ${reasons.join(', ') || 'sem observações relevantes'}.`,
    monitor: `Foram detectadas alterações leves que merecem acompanhamento. Motivos: ${reasons.join(', ')}. Recomendamos monitorar sintomas e repetir o teste no intervalo sugerido.`,
    procurar_medico: `O padrão de resultados sugere que uma avaliação clínica pode ser indicada. Motivos: ${reasons.join(', ')}. Leve este relatório ao profissional.`,
    urgencia: `Resultados com alterações relevantes e/ou sinais de risco. Motivos: ${reasons.join(', ')}. Procure atendimento de saúde imediatamente.`,
  }

  return {
    category,
    shortMessage: shortByCategory[category] || shortByCategory.normal,
    detailedMessage: detailedByCategory[category] || detailedByCategory.normal,
    recommendedRetestDays: retestDays,
  }
}

/**
 * Gera um feedback de triagem a partir das métricas resumidas do teste.
 * Retorna um objeto com categoria, mensagem curta e mensagem detalhada (em português).
 */
export const generateFeedbackFromSummary = (summary = {}) => {
  const accuracy = toNumber(summary.accuracyPercent)
  const errorCount = toNumber(summary.errorCount)
  const avgLatency = toNumber(summary.averageLatencyMs)
  const completionTime = toNumber(summary.completionTimeMs)

  const reasons = []

  if (accuracy <= 0) reasons.push('pontuação muito baixa')
  if (accuracy < 10) reasons.push('percentual de acertos muito baixo')
  if (accuracy >= 10 && accuracy < 25) reasons.push('percentual de acertos abaixo do esperado')
  if (avgLatency > 3000) reasons.push('tempos de resposta lentos')
  if (completionTime > 5 * 60 * 1000) reasons.push('duração atípica do teste')
  if (errorCount >= 6) reasons.push('erros frequentes durante o teste')

  // Regras simples para definição de categoria
  // Ajuste essas regras conforme normas e dados normativos reais.
  if (accuracy < 10 || errorCount > 10) {
    return buildFeedbackMessages({ category: 'urgencia', reasons, retestDays: null })
  }

  if ((accuracy >= 10 && accuracy < 25) || errorCount >= 6 || avgLatency > 3000) {
    return buildFeedbackMessages({ category: 'procurar_medico', reasons, retestDays: null })
  }

  if ((accuracy >= 25 && accuracy < 40) || (errorCount >= 3 && errorCount < 6) || avgLatency > 2000) {
    return buildFeedbackMessages({ category: 'monitor', reasons, retestDays: 90 })
  }

  return buildFeedbackMessages({ category: 'normal', reasons, retestDays: 365 })
}

/**
 * Retorna o feedback já formatado a partir do registro de resultado (inclui métricas convertidas).
 */
export const getFeedbackForResult = (registro) => {
  const formatted = formatarResultadoTeste(registro)
  const feedback = generateFeedbackFromSummary(formatted)

  return {
    ...formatted,
    feedback,
  }
}
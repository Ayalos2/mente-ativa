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
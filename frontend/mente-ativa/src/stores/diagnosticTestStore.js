import { computed, reactive } from 'vue'

const state = reactive({
  session: null,
  clickLogs: [],
  responseLogs: [],
})

const makeStamp = () => ({
  timestampMs: Date.now(),
  timestampIso: new Date().toISOString(),
})

const makeEventId = (prefix) => `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`

export function useDiagnosticTestStore() {
  const reset = () => {
    state.session = null
    state.clickLogs = []
    state.responseLogs = []
  }

  const startSession = ({ testId, testName, testType, userProfile, metadata }) => {
    reset()

    state.session = {
      sessionId: makeEventId(testId),
      testId,
      testName,
      testType,
      metadata: metadata || {},
      user: {
        uid: userProfile?.uid || null,
        email: userProfile?.email || null,
        nome: userProfile?.nome || null,
      },
      startedAtMs: Date.now(),
      startedAtIso: new Date().toISOString(),
    }
  }

  const logClick = (payload) => {
    const entry = {
      id: makeEventId('click'),
      type: 'click',
      ...makeStamp(),
      ...payload,
    }

    state.clickLogs.push(entry)
    return entry
  }

  const logResponse = (payload) => {
    const entry = {
      id: makeEventId('response'),
      type: 'response',
      ...makeStamp(),
      ...payload,
    }

    state.responseLogs.push(entry)
    return entry
  }

  const buildExportPayload = (summary = {}, extras = {}) => {
    if (!state.session) {
      return null
    }

    return {
      exportVersion: '1.0',
      ...state.session,
      summary,
      clickLogs: [...state.clickLogs],
      responseLogs: [...state.responseLogs],
      exportedAtMs: Date.now(),
      exportedAtIso: new Date().toISOString(),
      ...extras,
    }
  }

  const finishSession = (summary = {}, extras = {}) => buildExportPayload(summary, extras)

  const currentExport = computed(() => buildExportPayload())

  return {
    state,
    startSession,
    logClick,
    logResponse,
    finishSession,
    buildExportPayload,
    reset,
    currentExport,
  }
}

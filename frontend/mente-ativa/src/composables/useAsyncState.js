import { ref } from 'vue'

export function useAsyncState(initialState = {}) {
  const data = ref(initialState.data || null)
  const loading = ref(initialState.loading || false)
  const error = ref(initialState.error || '')

  const setLoading = (value) => {
    loading.value = value
  }

  const setError = (value) => {
    error.value = value
  }

  const setData = (value) => {
    data.value = value
  }

  const reset = () => {
    data.value = initialState.data || null
    loading.value = initialState.loading || false
    error.value = initialState.error || ''
  }

  const execute = async (asyncFunction) => {
    try {
      loading.value = true
      error.value = ''
      const result = await asyncFunction()
      data.value = result
      return result
    } catch (err) {
      error.value = err?.message || 'Ocorreu um erro inesperado.'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    data,
    loading,
    error,
    setLoading,
    setError,
    setData,
    reset,
    execute
  }
}
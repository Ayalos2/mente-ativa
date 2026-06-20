import axios from 'axios'
import { onAuthStateChanged } from 'firebase/auth'
import { auth } from '../config/firebase'

const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const firebaseTokenStorageKey = 'firebaseIdToken'

const waitForFirebaseUser = () => new Promise((resolve) => {
  if (auth?.currentUser) {
    resolve(auth.currentUser)
    return
  }

  if (!auth) {
    resolve(null)
    return
  }

  const unsubscribe = onAuthStateChanged(auth, (user) => {
    unsubscribe()
    resolve(user)
  })

  setTimeout(() => resolve(auth.currentUser), 4000)
})

const getAuthHeaders = async () => {
  const storedToken = sessionStorage.getItem(firebaseTokenStorageKey)
  const currentUser = auth?.currentUser || await waitForFirebaseUser()

  if (currentUser) {
    const token = await currentUser.getIdToken()
    sessionStorage.setItem(firebaseTokenStorageKey, token)

    return {
      Authorization: `Bearer ${token}`,
    }
  }

  if (storedToken) {
    return {
      Authorization: `Bearer ${storedToken}`,
    }
  }

  throw new Error('Usuário não autenticado no Firebase')
}

export const vincularPacientePorEmail = async (patientEmail) => {
  const headers = await getAuthHeaders()

  return axios.post(
    `${apiBaseUrl}/doctor-links/link`,
    { patientEmail },
    { headers }
  )
}

export const carregarPacientesDoMedico = async () => {
  const headers = await getAuthHeaders()

  return axios.get(`${apiBaseUrl}/doctor-links/patients`, {
    headers,
  })
}

export const carregarTestesDoPaciente = async (patientUid) => {
  const headers = await getAuthHeaders()

  return axios.get(`${apiBaseUrl}/doctor-links/patients/${patientUid}/tests`, {
    headers,
  })
}

export const carregarResumoClinicoPaciente = async (patientUid) => {
  const headers = await getAuthHeaders()

  return axios.get(`${apiBaseUrl}/doctor-links/patients/${patientUid}/summary`, {
    headers,
  })
}

export const requestLinkDoctor = async (doctorUid) => {
  const headers = await getAuthHeaders()

  return axios.post(
    `${apiBaseUrl}/doctor-links/request`,
    { doctorUid },
    { headers }
  )
}

export const carregarMeusMedicos = async () => {
  const headers = await getAuthHeaders()

  return axios.get(`${apiBaseUrl}/doctor-links/my-doctors`, {
    headers,
  })
}

export const carregarMeuResumoSaude = async () => {
  const headers = await getAuthHeaders()

  return axios.get(`${apiBaseUrl}/doctor-links/my-health-summary`, {
    headers,
  })
}

// ========== NOVAS FUNÇÕES ==========

/**
 * Médico gera o resumo LLM do paciente
 */
export const gerarResumoPaciente = async (patientUid) => {
  const headers = await getAuthHeaders()

  return axios.post(`${apiBaseUrl}/doctor-links/patients/${patientUid}/generate-summary`, {}, {
    headers,
  })
}

/**
 * Médico salva o diagnóstico textual do paciente
 */
export const salvarDiagnosticoPaciente = async (patientUid, diagnosis) => {
  const headers = await getAuthHeaders()

  return axios.post(
    `${apiBaseUrl}/doctor-links/patients/${patientUid}/diagnosis`,
    { diagnosis },
    { headers }
  )
}

/**
 * Médico visualiza o diagnóstico salvo de um paciente
 */
export const carregarDiagnosticoPaciente = async (patientUid) => {
  const headers = await getAuthHeaders()

  return axios.get(`${apiBaseUrl}/doctor-links/patients/${patientUid}/diagnosis`, {
    headers,
  })
}

/**
 * Médico disponibiliza o resumo LLM e diagnóstico para o paciente visualizar
 */
export const publicarResumoParaPaciente = async (patientUid) => {
  const headers = await getAuthHeaders()

  return axios.post(`${apiBaseUrl}/doctor-links/patients/${patientUid}/publish-summary`, {}, {
    headers,
  })
}

/**
 * Paciente visualiza seu diagnóstico médico (se disponibilizado)
 */
export const carregarMeuDiagnostico = async () => {
  const headers = await getAuthHeaders()

  return axios.get(`${apiBaseUrl}/doctor-links/my-health-summary`, {
    headers,
  })
}
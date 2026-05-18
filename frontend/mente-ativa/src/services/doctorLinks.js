import axios from 'axios'
import { auth } from '../config/firebase'

const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const getAuthHeaders = async () => {
  const currentUser = auth.currentUser

  if (!currentUser) {
    throw new Error('Usuário não autenticado no Firebase')
  }

  const token = await currentUser.getIdToken()

  return {
    Authorization: `Bearer ${token}`,
  }
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

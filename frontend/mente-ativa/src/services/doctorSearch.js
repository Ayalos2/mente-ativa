import { collection, getDocs, query, where, limit } from 'firebase/firestore'
import { db, isFirebaseConfigured } from '../config/firebase'

/**
 * Busca médicos (especialistas) por prefixo de nome.
 * Faz uma busca simples no cliente sobre os primeiros documentos encontrados.
 */
export const searchDoctorsByName = async (prefix = '', max = 20) => {
  if (!isFirebaseConfigured || !db) return []
  const p = (prefix || '').trim().toLowerCase()
  if (!p) return []

  const q = query(collection(db, 'usuarios'), where('cargo', '==', 'especialista'), limit(max))
  const snapshot = await getDocs(q)

  const results = snapshot.docs
    .map((d) => ({ uid: d.id, ...d.data() }))
    .filter((doc) => (doc.nome || '').toLowerCase().includes(p))

  return results
}

export default { searchDoctorsByName }

import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { signInWithEmailAndPassword, signOut, onAuthStateChanged } from 'firebase/auth'
import { doc, getDoc, setDoc } from 'firebase/firestore'
import { auth, db } from '../config/firebase'

const userProfile = ref(null)
const loading = ref(true)
const error = ref('')

export function useAuth() {
  const router = useRouter()

  const isAuthenticated = computed(() => {
    if (!userProfile.value) return false
    return Boolean(userProfile.value?.email || userProfile.value?.uid || userProfile.value?.nome)
  })

  const isEspecialista = computed(() => userProfile.value?.cargo === 'especialista')
  const isPaciente = computed(() => !userProfile.value?.cargo || userProfile.value?.cargo === 'paciente')

  const initializeAuth = async () => {
    try {
      const storedUser = sessionStorage.getItem('userProfile')
      
      if (storedUser) {
        const parsedUser = JSON.parse(storedUser)
        
        // Atualizar dados do Firestore se necessário
        if (parsedUser?.uid && (!parsedUser.cargo || parsedUser.cargo === 'paciente')) {
          try {
            const userDoc = await getDoc(doc(db, 'usuarios', parsedUser.uid))
            if (userDoc.exists()) {
              const userDocData = userDoc.data() || {}
              parsedUser.cargo = userDocData.cargo || parsedUser.cargo
              parsedUser.nome = userDocData.nome || parsedUser.nome
              parsedUser.foto = userDocData.foto || parsedUser.foto
              sessionStorage.setItem('userProfile', JSON.stringify(parsedUser))
            }
          } catch (err) {
            console.warn('Não foi possível atualizar perfil do usuário:', err)
          }
        }
        
        userProfile.value = parsedUser
      }
    } catch (err) {
      console.error('Erro ao inicializar autenticação:', err)
      sessionStorage.removeItem('userProfile')
    } finally {
      loading.value = false
    }
  }

  const loginWithEmail = async (email, password) => {
    try {
      error.value = ''
      const firebaseSession = await signInWithEmailAndPassword(auth, email, password)
      const displayName = firebaseSession.user.displayName || email

      const profile = {
        email: firebaseSession.user.email,
        nome: displayName,
        provedor: 'email',
        uid: firebaseSession.user.uid,
        cargo: 'paciente',
      }

      // Buscar dados adicionais do Firestore
      try {
        const userDocRef = doc(db, 'usuarios', firebaseSession.user.uid)
        const userDoc = await getDoc(userDocRef)
        if (userDoc.exists()) {
          const data = userDoc.data()
          profile.cargo = data.cargo || profile.cargo
          profile.nome = data.nome || profile.nome
        }
      } catch (err) {
        console.warn('Não foi possível ler documento do usuário:', err)
      }

      sessionStorage.setItem('userProfile', JSON.stringify(profile))
      userProfile.value = profile

      return profile
    } catch (err) {
      const message = getErrorMessage(err.code)
      error.value = message
      throw new Error(message)
    }
  }

  const loginWithGoogle = async (googleUser) => {
    try {
      error.value = ''
      
      const profile = {
        email: googleUser.user.email,
        nome: googleUser.user.nome || googleUser.user.displayName || googleUser.user.email,
        provedor: 'google',
        uid: googleUser.user.uid,
        foto: googleUser.user.foto || googleUser.user.photoURL || null,
        cargo: 'paciente',
      }

      // Salvar/atualizar no Firestore
      try {
        const userDocRef = doc(db, 'usuarios', googleUser.user.uid)
        const userDoc = await getDoc(userDocRef)
        
        if (userDoc.exists()) {
          const data = userDoc.data()
          profile.cargo = data.cargo || profile.cargo
          profile.nome = data.nome || profile.nome
          profile.foto = data.foto || profile.foto
        }

        await setDoc(userDocRef, {
          uid: googleUser.user.uid,
          email: googleUser.user.email,
          nome: profile.nome,
          cargo: profile.cargo,
          foto: profile.foto,
          provedor: 'google',
          createdAtMs: Date.now(),
          createdAtIso: new Date().toISOString(),
        }, { merge: true })
      } catch (err) {
        console.warn('Falha ao acessar/atualizar documento usuário:', err)
      }

      sessionStorage.setItem('userProfile', JSON.stringify(profile))
      userProfile.value = profile

      return profile
    } catch (err) {
      error.value = 'Falha no login Google. Verifique a configuração do Firebase.'
      throw err
    }
  }

  const logout = async () => {
    try {
      await signOut(auth)
      sessionStorage.removeItem('userProfile')
      sessionStorage.removeItem('firebaseIdToken')
      userProfile.value = null
      router.push('/login')
    } catch (err) {
      console.error('Erro ao fazer logout:', err)
      throw err
    }
  }

  const getErrorMessage = (code) => {
    switch (code) {
      case 'auth/invalid-credential':
      case 'auth/wrong-password':
      case 'auth/user-not-found':
        return 'E-mail ou senha incorretos.'
      case 'auth/invalid-email':
        return 'E-mail inválido.'
      default:
        return 'Não foi possível entrar. Verifique se o Firebase Auth está configurado.'
    }
  }

  return {
    userProfile,
    loading,
    error,
    isAuthenticated,
    isEspecialista,
    isPaciente,
    initializeAuth,
    loginWithEmail,
    loginWithGoogle,
    logout,
    setError: (msg) => { error.value = msg }
  }
}
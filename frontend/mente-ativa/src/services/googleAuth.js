import { GoogleAuthProvider, signInWithPopup } from 'firebase/auth'
import { auth, isFirebaseConfigured } from '../config/firebase'

const googleProvider = new GoogleAuthProvider()

googleProvider.setCustomParameters({
  prompt: 'select_account',
})

export const loginComGoogle = async () => {
  if (!isFirebaseConfigured || !auth) {
    throw new Error('Firebase nao configurado')
  }

  const result = await signInWithPopup(auth, googleProvider)

  const token = await result.user.getIdToken()

  return {
    token,
    user: {
      uid: result.user.uid,
      nome: result.user.displayName,
      email: result.user.email,
      foto: result.user.photoURL,
    },
  }
}

import { initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

const firebaseEnvKeys = [
  'VITE_FIREBASE_API_KEY',
  'VITE_FIREBASE_AUTH_DOMAIN',
  'VITE_FIREBASE_PROJECT_ID',
  'VITE_FIREBASE_APP_ID',
]

const hasMissingFirebaseConfig = firebaseEnvKeys.some((key) => !import.meta.env[key])

if (hasMissingFirebaseConfig) {
  console.warn('Firebase nao configurado. Defina as variaveis VITE_FIREBASE_* para habilitar login com Google.')
}

const app = hasMissingFirebaseConfig ? null : initializeApp(firebaseConfig)

export const auth = app ? getAuth(app) : null
export const isFirebaseConfigured = !hasMissingFirebaseConfig

import { initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'
import { getFirestore } from 'firebase/firestore'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'AIzaSyAasc6n9L6rlrb1q7oQ7fBYFgd2JE31zeo',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'mente-ativa-827bd.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'mente-ativa-827bd',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || 'mente-ativa-827bd.firebasestorage.app',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '207875687436',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '1:207875687436:web:a8f3f01c3f28ea80f75a29',
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || 'G-87J8Y0P00R',
}

const app = initializeApp(firebaseConfig)

export const auth = getAuth(app)
export const db = getFirestore(app)
export const isFirebaseConfigured = Boolean(firebaseConfig.apiKey && firebaseConfig.projectId && firebaseConfig.appId)

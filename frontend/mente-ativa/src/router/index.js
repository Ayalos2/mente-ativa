import { createRouter, createWebHistory } from 'vue-router'
import { onAuthStateChanged } from 'firebase/auth'
import { auth } from '../config/firebase'
import Home from '../views/Home.vue'

const isUsuarioAutenticado = () => {
  const rawProfile = sessionStorage.getItem('userProfile')

  if (!rawProfile) {
    return false
  }

  try {
    const profile = JSON.parse(rawProfile)
    return Boolean(profile?.email || profile?.uid || profile?.nome)
  } catch {
    return false
  }
}

const aguardarUsuarioFirebase = () => new Promise((resolve) => {
  if (auth.currentUser) {
    resolve(auth.currentUser)
    return
  }

  const unsub = onAuthStateChanged(auth, (user) => {
    unsub()
    resolve(user)
  })

  setTimeout(() => resolve(auth.currentUser), 4000)
})

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/testes',
    name: 'TestesCognitivos',
    component: () => import('../views/TestesCognitivos.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue') 
  },
  {
    path: '/cadastro',
    name: 'Cadastro',
    component: () => import('../views/Cadastro.vue')
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile/historico',
    name: 'HistoricoTestes',
    component: () => import('../views/HistoricoTestes.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile/edit',
    name: 'EditProfile',
    component: () => import('../views/EditProfile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile/privacy-security',
    name: 'PrivacySecurity',
    component: () => import('../views/PrivacySecurity.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/teste/memorias',
    name: 'TesteMemorias',
    redirect: '/testes/memoria-curto-prazo'
  },
  {
    path: '/teste/alzheimer',
    name: 'TesteAlzheimer',
    redirect: '/testes'
  },
  {
    path: '/testes/memoria-curto-prazo',
    name: 'TesteMemoriaCurtoPrazo',
    component: () => import('../views/TesteMemoriaCurtoPrazo.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/testes/fluencia-semantica',
    name: 'TesteFluenciaSemantica',
    component: () => import('../views/TesteFluenciaSemantica.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/testes/atencao-alternada',
    name: 'TesteAtencaoAlternada',
    component: () => import('../views/TesteAtencaoAlternada.vue'),
    meta: { requiresAuth: true }
  }
  // Futuramente colocaremos a rota '/teste' e '/login' aqui!
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) {
    return true
  }

  if (isUsuarioAutenticado()) {
    return true
  }

  const firebaseUser = await aguardarUsuarioFirebase()

  if (firebaseUser) {
    return true
  }

  return {
    path: '/login',
    query: { redirect: to.fullPath }
  }
})

export default router
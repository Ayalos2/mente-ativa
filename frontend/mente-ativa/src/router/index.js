import { createRouter, createWebHistory } from 'vue-router'
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

router.beforeEach((to) => {
  if (!to.meta.requiresAuth) {
    return true
  }

  if (isUsuarioAutenticado()) {
    return true
  }

  return {
    path: '/login',
    query: { redirect: to.fullPath }
  }
})

export default router
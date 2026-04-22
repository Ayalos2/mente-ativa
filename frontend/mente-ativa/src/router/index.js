import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
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
    component: () => import('../views/Profile.vue')
  }
  // Futuramente colocaremos a rota '/teste' e '/login' aqui!
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
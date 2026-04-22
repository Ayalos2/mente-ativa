<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import GoogleLoginButton from '../components/auth/GoogleLoginButton.vue'


const router = useRouter()
const email = ref('')
const senha = ref('')
const carregando = ref(false)

const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const realizarLogin = async () => {
  carregando.value = true
  try {
    const resposta = await axios.post(`${apiBaseUrl}/login`, {
      email: email.value,
      senha: senha.value
    })

    if (resposta.data.status === 'sucesso') {
      alert('Bem-vindo, ' + resposta.data.usuario)
      router.push('/')
    } else {
      alert(resposta.data.mensagem)
    }
  } catch (error) {
    alert('Erro ao conectar com o servidor. Verifique se o backend está rodando!')
  } finally {
    carregando.value = false
  }
}

const lidarComSucessoGoogle = async (resultado) => {
  try {
    const resposta = await axios.post(`${apiBaseUrl}/auth/google`, {
      credential: resultado.token,
      user: resultado.user,
    })

    if (resposta.data.status === 'sucesso') {
      alert('Bem-vindo, ' + resposta.data.usuario)
      router.push('/')
      return
    }
    alert(resposta.data.mensagem || 'Nao foi possivel entrar com Google.')
  } catch (error) {
    alert('Falha no login Google. Verifique a configuracao do Firebase e do backend.')
  }
}

</script>

<template>
  <div class="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
    
    <div class="sm:mx-auto sm:w-full sm:max-w-md text-center">
      <div @click="router.push('/')" class="cursor-pointer inline-flex items-center gap-2 mb-6 select-none">
        <div class="bg-emerald-600 p-2 rounded-lg shadow-md">
          <span class="text-white text-xl">🧠</span>
        </div>
        <span class="text-2xl font-bold text-slate-800 tracking-tight">Mente Ativa</span>
      </div>
      <h2 class="text-3xl font-extrabold text-slate-900 tracking-tight">
        Acesso ao Painel
      </h2>
      <p class="mt-2 text-sm text-slate-600">
        Área exclusiva para profissionais de saúde e responsáveis.
      </p>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-white py-8 px-4 shadow-xl shadow-slate-200/50 sm:rounded-3xl sm:px-10 border border-slate-100">
        <form class="space-y-6" @submit.prevent="realizarLogin">
          
          <div>
            <label for="email" class="block text-sm font-semibold text-slate-700">E-mail</label>
            <div class="mt-1">
              <input 
                v-model="email"
                id="email" 
                type="email" 
                required 
                placeholder="exemplo@email.com"
                class="appearance-none block w-full px-4 py-3 border border-slate-300 rounded-xl shadow-sm placeholder-slate-400 focus:outline-none focus:ring-emerald-500 focus:border-emerald-500 text-slate-900 transition-all"
              />
            </div>
          </div>

          <div>
            <label for="password" class="block text-sm font-semibold text-slate-700">Senha</label>
            <div class="mt-1">
              <input 
                v-model="senha"
                id="password" 
                type="password" 
                required 
                placeholder="••••••••"
                class="appearance-none block w-full px-4 py-3 border border-slate-300 rounded-xl shadow-sm placeholder-slate-400 focus:outline-none focus:ring-emerald-500 focus:border-emerald-500 text-slate-900 transition-all"
              />
            </div>
          </div>

          <div class="flex items-center justify-between">
            <div class="text-sm">
              <a href="#" class="font-medium text-emerald-600 hover:text-emerald-500 transition-colors">
                Esqueceu a senha?
              </a>
            </div>
          </div>

          <div>
            <button 
              type="submit" 
              :disabled="carregando"
              class="w-full flex justify-center py-3.5 px-4 border border-transparent rounded-2xl shadow-sm text-lg font-bold text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-4 focus:ring-emerald-300 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="!carregando">Entrar no Sistema</span>
              <span v-else class="flex items-center gap-2">
                <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Autenticando...
              </span>
            </button>
          </div>
        </form>

        <div class="my-6 relative">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-slate-200"></div>
          </div>
          <div class="relative flex justify-center text-sm">
            <span class="px-2 bg-white text-slate-500 font-medium">ou continue com</span>
          </div>
        </div>

        <div class="flex justify-center">
          <GoogleLoginButton @success="lidarComSucessoGoogle" @error="() => alert('Falha no login Google. Verifique a configuracao do Firebase.')" />
        </div>

        <div class="mt-6">
          <div class="relative">
            <div class="absolute inset-0 flex items-center">
              <div class="w-full border-t border-slate-200"></div>
            </div>
            <div class="relative flex justify-center text-sm">
              <span class="px-2 bg-white text-slate-500 font-medium">Não tem uma conta?</span>
            </div>
          </div>

          <div class="mt-6">
            <button class="w-full flex justify-center py-3 px-4 border-2 border-slate-200 rounded-2xl text-sm font-bold text-slate-700 bg-white hover:bg-slate-50 transition-all">
              Solicitar Acesso Especialista
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { useAuth } from '../composables'
import { useAsyncState } from '../composables'

// Exemplo de uso do useAuth
const {
  userProfile,
  isAuthenticated,
  isEspecialista,
  isPaciente,
  loading: authLoading,
  initializeAuth,
  loginWithEmail,
  loginWithGoogle,
  logout
} = useAuth()

// Exemplo de uso do useAsyncState
const {
  data: asyncData,
  loading: asyncLoading,
  error: asyncError,
  execute: executeAsync
} = useAsyncState()

// Inicializar auth quando o componente montar
initializeAuth()

// Exemplo de função assíncrona
const fetchData = async () => {
  await executeAsync(async () => {
    // Simulando uma chamada API
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ message: 'Dados carregados com sucesso!' })
      }, 2000)
    })
  })
}

const handleLogin = async () => {
  try {
    await loginWithEmail('usuario@email.com', 'senha123')
  } catch (error) {
    console.error('Erro no login:', error)
  }
}

const handleLogout = async () => {
  try {
    await logout()
  } catch (error) {
    console.error('Erro no logout:', error)
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 p-8">
    <div class="max-w-4xl mx-auto space-y-8">
      
      <h1 class="text-3xl font-bold text-slate-900 mb-8">Exemplos de Composables</h1>

      <!-- useAuth Example -->
      <AppCard title="useAuth" subtitle="Gerenciamento de autenticação">
        <div class="space-y-4">
          <div class="p-4 bg-slate-50 rounded-xl">
            <p class="text-sm font-semibold text-slate-700 mb-2">Status da Autenticação:</p>
            <p class="text-slate-900">Autenticado: <strong>{{ isAuthenticated }}</strong></p>
            <p v-if="userProfile" class="text-slate-900">Usuário: <strong>{{ userProfile.nome || userProfile.email }}</strong></p>
            <p class="text-slate-900">Tipo: <strong>{{ isEspecialista ? 'Especialista' : isPaciente ? 'Paciente' : 'Não definido' }}</strong></p>
          </div>

          <div class="flex flex-wrap gap-3">
            <AppButton @click="handleLogin" variant="primary">Simular Login</AppButton>
            <AppButton @click="handleLogout" variant="danger">Logout</AppButton>
          </div>
        </div>
      </AppCard>

      <!-- useAsyncState Example -->
      <AppCard title="useAsyncState" subtitle="Gerenciamento de estado assíncrono">
        <div class="space-y-4">
          <div class="p-4 bg-slate-50 rounded-xl">
            <p class="text-sm font-semibold text-slate-700 mb-2">Estado:</p>
            <p class="text-slate-900">Loading: <strong>{{ asyncLoading }}</strong></p>
            <p v-if="asyncError" class="text-red-700">Erro: <strong>{{ asyncError }}</strong></p>
            <p v-if="asyncData" class="text-slate-900">Dados: <strong>{{ asyncData.message }}</strong></p>
          </div>

          <AppButton 
            @click="fetchData" 
            variant="primary"
            :loading="asyncLoading"
          >
            Carregar Dados
          </AppButton>
        </div>
      </AppCard>

    </div>
  </div>
</template>
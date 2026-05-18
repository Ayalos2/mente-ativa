<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { createUserWithEmailAndPassword, updateProfile } from 'firebase/auth'
import { doc, setDoc } from 'firebase/firestore'
import { auth, db } from '../config/firebase'

const router = useRouter()
const route = useRoute()

// Estados do formulário
const nome = ref('')
const email = ref('')
const senha = ref('')
const confirmSenha = ref('')
const cargo = ref(route.query.role || 'paciente') // Valor padrão pode vir da query
const crmcrp = ref('')
const carregando = ref(false)
const erroCadastro = ref('')

const realizarCadastro = async () => {
  erroCadastro.value = ''

  if (senha.value !== confirmSenha.value) {
    erroCadastro.value = 'As senhas não coincidem.'
    return
  }

  carregando.value = true

  try {
    const credential = await createUserWithEmailAndPassword(auth, email.value.trim(), senha.value)

    await updateProfile(credential.user, {
      displayName: nome.value.trim(),
    })

    const userProfile = {
      uid: credential.user.uid,
      email: credential.user.email,
      nome: nome.value.trim(),
      provedor: 'email',
      cargo: cargo.value,
      crmcrp: cargo.value === 'especialista' ? crmcrp.value.trim() : '',
    }

    sessionStorage.setItem('userProfile', JSON.stringify(userProfile))

    await setDoc(doc(db, 'usuarios', credential.user.uid), {
      uid: credential.user.uid,
      email: credential.user.email,
      nome: nome.value.trim(),
      cargo: cargo.value,
      crmcrp: cargo.value === 'especialista' ? crmcrp.value.trim() : '',
      provedor: 'email',
      createdAtMs: Date.now(),
      createdAtIso: new Date().toISOString(),
    }, { merge: true })

    router.push('/profile')
  } catch (error) {
    console.error('Erro ao criar conta:', error)
    erroCadastro.value = error?.message || 'Nao foi possivel criar a conta.'
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans">
    
    <div class="absolute top-8 left-8">
      <button @click="router.push('/')" class="text-slate-500 hover:text-emerald-600 flex items-center gap-2 transition-colors font-medium">
        <span>←</span> Voltar para a Home
      </button>
    </div>

    <div class="sm:mx-auto sm:w-full sm:max-w-md text-center">
      <div class="inline-flex items-center gap-2 mb-4 select-none">
        <div class="bg-emerald-600 p-2 rounded-lg shadow-md">
          <span class="text-white text-xl font-bold">M</span>
        </div>
        <span class="text-2xl font-bold text-slate-800 tracking-tight">Mente Ativa</span>
      </div>
      <h2 class="text-3xl font-extrabold text-slate-900 tracking-tight">Crie sua conta</h2>
      <p class="mt-2 text-sm text-slate-600">Comece a monitorar a saúde cognitiva hoje mesmo.</p>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-lg">
      <div class="bg-white py-10 px-6 shadow-xl shadow-slate-200/50 sm:rounded-3xl sm:px-12 border border-slate-100">
        
        <form class="grid grid-cols-1 gap-y-6 sm:grid-cols-2 sm:gap-x-4" @submit.prevent="realizarCadastro">
          <div v-if="erroCadastro" class="sm:col-span-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
            {{ erroCadastro }}
          </div>
          
          <div class="sm:col-span-2">
            <label class="block text-sm font-semibold text-slate-700">Nome Completo</label>
            <input v-model="nome" type="text" required placeholder="Dr(a). Nome Sobrenome" 
              class="mt-1 block w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-emerald-500 focus:border-emerald-500 text-slate-900 transition-all" />
          </div>

          <div class="sm:col-span-2">
            <label class="block text-sm font-semibold text-slate-700">E-mail Profissional</label>
            <input v-model="email" type="email" required placeholder="contato@clinica.com" 
              class="mt-1 block w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-emerald-500 focus:border-emerald-500 text-slate-900 transition-all" />
          </div>

          <div class="sm:col-span-2">
            <label class="block text-sm font-semibold text-slate-700">Função</label>
            <select v-model="cargo" class="mt-1 block w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-emerald-500 focus:border-emerald-500 bg-white text-slate-900">
              <option value="especialista">Especialista (Médico/Psicólogo)</option>
              <option value="responsavel">Responsável Familiar</option>
              <option value="administrador">Administrador</option>
              <option value="pesquisador">Pesquisador</option>
              <option value="paciente">Paciente</option>
              <option value="outro">Outro</option>
            </select>
          </div>

          <div class="sm:col-span-2" v-if="cargo === 'especialista'">
            <label class="block text-sm font-semibold text-slate-700">CRM/CRP</label>
            <input v-model="crmcrp" type="text" required placeholder="CRM/CRP" 
              class="mt-1 block w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-emerald-500 focus:border-emerald-500 text-slate-900 transition-all" />
          </div>

          <div>
            <label class="block text-sm font-semibold text-slate-700">Senha</label>
            <input v-model="senha" type="password" required placeholder="••••••••" 
              class="mt-1 block w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-emerald-500 focus:border-emerald-500 text-slate-900 transition-all" />
          </div>

          <div>
            <label class="block text-sm font-semibold text-slate-700">Confirmar Senha</label>
            <input v-model="confirmSenha" type="password" required placeholder="••••••••" 
              class="mt-1 block w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-emerald-500 focus:border-emerald-500 text-slate-900 transition-all" />
          </div>

          <div class="sm:col-span-2 mt-4">
            <button 
              type="submit" 
              :disabled="carregando"
              class="w-full bg-emerald-600 hover:bg-emerald-700 text-white px-8 py-4 rounded-2xl text-lg font-bold transition-all shadow-lg shadow-emerald-200 active:scale-95 disabled:opacity-50"
            >
              <span v-if="!carregando">Criar Minha Conta</span>
              <span v-else class="flex justify-center items-center gap-2">
                <svg class="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Processando...
              </span>
            </button>
          </div>
        </form>

      </div>
    </div>
  </div>
</template>
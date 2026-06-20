<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { createUserWithEmailAndPassword, updateProfile } from 'firebase/auth'
import { doc, setDoc } from 'firebase/firestore'
import { auth, db } from '../config/firebase'
import AppButton from '../components/base/AppButton.vue'
import AppInput from '../components/base/AppInput.vue'

const router = useRouter()
const route = useRoute()

// Etapas: 'selecao' -> 'formulario'
const etapa = ref(route.query.role ? 'formulario' : 'selecao')

// Estados do formulário
const nome = ref('')
const email = ref('')
const senha = ref('')
const confirmSenha = ref('')
const cargo = ref(route.query.role || '')
const crmcrp = ref('')
const carregando = ref(false)
const erroCadastro = ref('')

const tituloFormulario = computed(() => {
  if (cargo.value === 'especialista') return 'Cadastro do Profissional'
  if (cargo.value === 'paciente') return 'Cadastro do Paciente'
  return 'Crie sua conta'
})

const selecionarPerfil = (perfil) => {
  cargo.value = perfil
  etapa.value = 'formulario'
}

const voltarSelecao = () => {
  etapa.value = 'selecao'
  cargo.value = ''
  erroCadastro.value = ''
}

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
  <!-- ETAPA DE SELEÇÃO DE PERFIL -->
  <div v-if="etapa === 'selecao'" class="min-h-screen bg-slate-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans">
    
    <div class="absolute top-8 left-8">
      <button @click="router.push('/')" class="text-slate-500 hover:text-emerald-600 flex items-center gap-2 transition-colors font-medium">
        <span>←</span> Voltar para a Home
      </button>
    </div>

    <div class="sm:mx-auto sm:w-full sm:max-w-lg text-center mb-8">
      <div class="inline-flex items-center gap-2 mb-4 select-none">
        <div class="bg-emerald-600 p-2 rounded-lg shadow-md">
          <span class="text-white text-xl font-bold">M</span>
        </div>
        <span class="text-2xl font-bold text-slate-800 tracking-tight">Mente Ativa</span>
      </div>
      <h2 class="text-3xl font-extrabold text-slate-900 tracking-tight">Crie sua conta</h2>
      <p class="mt-2 text-sm text-slate-600">Selecione o tipo de perfil para começar.</p>
    </div>

    <div class="sm:mx-auto sm:w-full sm:max-w-lg">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
        
        <!-- Card Paciente -->
        <button
          @click="selecionarPerfil('paciente')"
          class="group bg-white rounded-3xl p-8 shadow-xl shadow-slate-200/50 border-2 border-slate-100 hover:border-emerald-400 hover:shadow-emerald-100/50 transition-all text-center"
        >
          <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-emerald-100 flex items-center justify-center group-hover:bg-emerald-200 transition-colors">
            <span class="text-4xl">👤</span>
          </div>
          <h3 class="text-xl font-bold text-slate-800 mb-2">Paciente</h3>
          <p class="text-sm text-slate-500 leading-relaxed">
            Acesse testes cognitivos, acompanhe seu histórico e monitore sua saúde mental.
          </p>
        </button>

        <!-- Card Médico/Especialista -->
        <button
          @click="selecionarPerfil('especialista')"
          class="group bg-white rounded-3xl p-8 shadow-xl shadow-slate-200/50 border-2 border-slate-100 hover:border-emerald-400 hover:shadow-emerald-100/50 transition-all text-center"
        >
          <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-sky-100 flex items-center justify-center group-hover:bg-sky-200 transition-colors">
            <span class="text-4xl">👨‍⚕️</span>
          </div>
          <h3 class="text-xl font-bold text-slate-800 mb-2">Médico / Especialista</h3>
          <p class="text-sm text-slate-500 leading-relaxed">
            Aplique testes, gerencie pacientes e acompanhe resultados detalhados.
          </p>
        </button>

      </div>
    </div>
  </div>

  <!-- ETAPA DE FORMULÁRIO PERSONALIZADO -->
  <div v-else class="min-h-screen bg-slate-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans">
    
    <div class="absolute top-8 left-8">
      <button @click="voltarSelecao" class="text-slate-500 hover:text-emerald-600 flex items-center gap-2 transition-colors font-medium">
        <span>←</span> Voltar
      </button>
    </div>

    <div class="sm:mx-auto sm:w-full sm:max-w-md text-center">
      <div class="inline-flex items-center gap-2 mb-4 select-none">
        <div class="bg-emerald-600 p-2 rounded-lg shadow-md">
          <span class="text-white text-xl font-bold">M</span>
        </div>
        <span class="text-2xl font-bold text-slate-800 tracking-tight">Mente Ativa</span>
      </div>
      <h2 class="text-3xl font-extrabold text-slate-900 tracking-tight">{{ tituloFormulario }}</h2>
      <p class="mt-2 text-sm text-slate-600">Preencha os dados abaixo para criar sua conta.</p>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-lg">
      <div class="bg-white py-10 px-6 shadow-xl shadow-slate-200/50 sm:rounded-3xl sm:px-12 border border-slate-100">
        
        <form class="space-y-6" @submit.prevent="realizarCadastro">
          <div v-if="erroCadastro" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
            {{ erroCadastro }}
          </div>

          <!-- Badge do perfil selecionado -->
          <div class="flex justify-center mb-2">
            <span
              v-if="cargo === 'paciente'"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-100 text-emerald-700 text-sm font-semibold"
            >
              <span>👤</span> Perfil: Paciente
            </span>
            <span
              v-else-if="cargo === 'especialista'"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sky-100 text-sky-700 text-sm font-semibold"
            >
              <span>👨‍⚕️</span> Perfil: Médico / Especialista
            </span>
          </div>
          
          <AppInput
            v-model="nome"
            type="text"
            label="Nome Completo"
            placeholder="Dr(a). Nome Sobrenome"
            required
          />

          <AppInput
            v-model="email"
            type="email"
            label="E-mail"
            placeholder="contato@clinica.com"
            required
          />

          <!-- Campo CRM/CRP apenas para especialista -->
          <div v-if="cargo === 'especialista'">
            <AppInput
              v-model="crmcrp"
              type="text"
              label="CRM / CRP"
              placeholder="Número do registro profissional"
              required
            />
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <AppInput
              v-model="senha"
              type="password"
              label="Senha"
              placeholder="••••••••"
              required
            />

            <AppInput
              v-model="confirmSenha"
              type="password"
              label="Confirmar Senha"
              placeholder="••••••••"
              required
            />
          </div>

          <div class="pt-2">
            <AppButton 
              type="submit" 
              :loading="carregando"
              variant="primary"
              size="lg"
              class="w-full"
            >
              <span v-if="!carregando">Criar Minha Conta</span>
              <template #loading>
                <span class="flex justify-center items-center gap-2">
                  <svg class="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  Processando...
                </span>
              </template>
            </AppButton>
          </div>
        </form>

      </div>
    </div>
  </div>
</template>
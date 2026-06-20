<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useRoute } from 'vue-router'
import { signInWithEmailAndPassword } from 'firebase/auth'
import { doc, setDoc, getDoc } from 'firebase/firestore'
import { auth, db } from '../config/firebase'
import GoogleLoginButton from '../components/auth/GoogleLoginButton.vue'
import AppButton from '../components/base/AppButton.vue'
import AppInput from '../components/base/AppInput.vue'

const firebaseTokenStorageKey = 'firebaseIdToken'


const router = useRouter()
const route = useRoute()
const email = ref('')
const senha = ref('')
const carregando = ref(false)

const mostrarErroLoginGoogle = () => {
  window.alert('Falha no login Google. Verifique a configuracao do Firebase.')
}

const realizarLogin = async () => {
  carregando.value = true
  try {
    const firebaseSession = await signInWithEmailAndPassword(auth, email.value.trim(), senha.value)
    const displayName = firebaseSession.user.displayName || email.value.trim()

    const userProfile = {
      email: firebaseSession.user.email,
      nome: displayName,
      provedor: 'email',
      uid: firebaseSession.user.uid,
      cargo: 'paciente',
    }

    try {
      const userDocRef = doc(db, 'usuarios', firebaseSession.user.uid)
      const userDoc = await getDoc(userDocRef)
      if (userDoc.exists()) {
        const data = userDoc.data()
        userProfile.cargo = data.cargo || userProfile.cargo
        userProfile.nome = data.nome || userProfile.nome
      }
    } catch (err) {
      console.warn('Nao foi possivel ler o documento do usuario para carregar cargo:', err)
    }

    sessionStorage.setItem('userProfile', JSON.stringify(userProfile))
    sessionStorage.setItem(firebaseTokenStorageKey, await firebaseSession.user.getIdToken())

    alert('Bem-vindo, ' + displayName)
    router.push(route.query.redirect || '/profile')
  } catch (error) {
    const firebaseError = error?.code || ''

    if (firebaseError === 'auth/invalid-credential' || firebaseError === 'auth/wrong-password' || firebaseError === 'auth/user-not-found') {
      alert('E-mail ou senha incorretos.')
    } else if (firebaseError === 'auth/invalid-email') {
      alert('E-mail inválido.')
    } else {
      console.error('Erro ao autenticar com Firebase:', error)
      alert('Nao foi possivel entrar com email e senha. Verifique se o Firebase Auth está configurado.')
    }
  } finally {
    carregando.value = false
  }
}

const lidarComSucessoGoogle = async (resultado) => {
  try {
    const userProfile = {
      email: resultado.user.email,
      nome: resultado.user.nome || resultado.user.displayName || resultado.user.email,
      provedor: 'google',
      uid: resultado.user.uid,
      foto: resultado.user.foto || resultado.user.photoURL || null,
      cargo: 'paciente',
    }

    try {
      const userDocRef = doc(db, 'usuarios', resultado.user.uid)
      const userDoc = await getDoc(userDocRef)
      if (userDoc.exists()) {
        const data = userDoc.data()
        userProfile.cargo = data.cargo || userProfile.cargo
        userProfile.nome = data.nome || userProfile.nome
        userProfile.foto = data.foto || userProfile.foto
      }

      // Garantir que exista/atualizar o documento do usuário no Firestore
      await setDoc(userDocRef, {
        uid: resultado.user.uid,
        email: resultado.user.email,
        nome: userProfile.nome,
        cargo: userProfile.cargo,
        foto: userProfile.foto,
        provedor: 'google',
        createdAtMs: Date.now(),
        createdAtIso: new Date().toISOString(),
      }, { merge: true })
    } catch (error) {
      console.warn('Falha ao acessar/atualizar documento usuario:', error)
    }

    sessionStorage.setItem('userProfile', JSON.stringify(userProfile))
    sessionStorage.setItem(firebaseTokenStorageKey, resultado.token)
    router.push(route.query.redirect || '/profile')
  } catch (error) {
    console.error('Falha no login Google:', error)
    alert('Falha no login Google. Verifique a configuracao do Firebase.')
  }
}

</script>

<template>
  <div class="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
    
    <div class="absolute top-8 left-8">
      <button @click="router.push('/')" class="text-slate-500 hover:text-emerald-600 flex items-center gap-2 transition-colors font-medium">
        <span>←</span> Voltar para a Home
      </button>
    </div>

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
          
          <AppInput
            v-model="email"
            id="email"
            type="email"
            label="E-mail"
            placeholder="exemplo@email.com"
            required
          />

          <AppInput
            v-model="senha"
            id="password"
            type="password"
            label="Senha"
            placeholder="••••••••"
            required
          />

          <div class="flex items-center justify-between">
            <div class="text-sm">
              <a href="#" class="font-medium text-emerald-600 hover:text-emerald-500 transition-colors">
                Esqueceu a senha?
              </a>
            </div>
          </div>

          <div>
            <AppButton 
              type="submit" 
              :loading="carregando"
              variant="primary"
              size="lg"
              class="w-full"
            >
              <span v-if="!carregando">Entrar no Sistema</span>
              <template #loading>
                <span class="flex items-center gap-2">
                  <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  Autenticando...
                </span>
              </template>
            </AppButton>
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
          <GoogleLoginButton @success="lidarComSucessoGoogle" @error="mostrarErroLoginGoogle" />
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
              <AppButton
                @click="router.push('/cadastro')"
                variant="ghost"
                size="lg"
                class="w-full"
              >
                Criar Conta
              </AppButton>
            </div>
          </div>
      </div>
    </div>
  </div>
</template>
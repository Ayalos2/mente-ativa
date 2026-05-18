<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { doc, setDoc, getDoc } from 'firebase/firestore'
import { db } from '../config/firebase'
import { getCurrentUserProfile } from '../services/sessionUser'
import { searchDoctorsByName } from '../services/doctorSearch'
import { requestLinkDoctor } from '../services/doctorLinks'

const router = useRouter()

const nome = ref('')
const apelido = ref('')
const email = ref('')
const emailSecundario = ref('')
const telefone = ref('')
const dataNascimento = ref('')
const genero = ref('')
const endereco = ref('')
const cidade = ref('')
const estado = ref('')
const fusoHorario = ref('')
const locale = ref('')
const cargo = ref('paciente')
const especialidade = ref('')
const crmcrp = ref('')
const instituicao = ref('')
const contatoEmergenciaNome = ref('')
const contatoEmergenciaRelacao = ref('')
const contatoEmergenciaTelefone = ref('')
const condicoesMedicas = ref('')
const medicamentos = ref('')
const consentCompartilhar = ref(false)
const preferenciasNotificacao = ref({ email: true, push: false })
const notasPrivadas = ref('')
const carregando = ref(false)
const mensagem = ref('')
const erro = ref('')

// Vincular médico (para pacientes)
const doctorQuery = ref('')
const doctorSuggestions = ref([])
const searchingDoctors = ref(false)
const linkMessage = ref('')
let doctorSearchTimer = null
const onDoctorInput = () => {
  linkMessage.value = ''
  doctorSuggestions.value = []

  if (doctorSearchTimer) clearTimeout(doctorSearchTimer)

  const q = doctorQuery.value.trim()
  if (!q) return

  doctorSearchTimer = setTimeout(async () => {
    try {
      searchingDoctors.value = true
      doctorSuggestions.value = await searchDoctorsByName(q, 20)
    } catch (e) {
      console.error('Erro ao buscar medicos:', e)
      doctorSuggestions.value = []
    } finally {
      searchingDoctors.value = false
    }
  }, 300)
}

const selectDoctorToLink = async (doctor) => {
  linkMessage.value = ''
  try {
    await requestLinkDoctor(doctor.uid)
    linkMessage.value = `Solicitação enviada para ${doctor.nome}.` 
    doctorSuggestions.value = []
    doctorQuery.value = ''
  } catch (e) {
    console.error('Erro ao solicitar vínculo:', e)
    linkMessage.value = e?.response?.data?.detail || 'Não foi possível enviar a solicitação.'
  }
}

onMounted(async () => {
  const perfil = getCurrentUserProfile()

  if (!perfil) {
    router.push('/login')
    return
  }

  // Preenche com dados do sessionStorage primeiro
  nome.value = perfil.nome || ''
  apelido.value = perfil.apelido || ''
  email.value = perfil.email || ''
  emailSecundario.value = perfil.emailSecundario || ''
  telefone.value = perfil.telefone || ''
  dataNascimento.value = perfil.dataNascimento || ''
  genero.value = perfil.genero || ''
  endereco.value = perfil.endereco || ''
  cidade.value = perfil.cidade || ''
  estado.value = perfil.estado || ''
  fusoHorario.value = perfil.fusoHorario || ''
  locale.value = perfil.locale || ''
  cargo.value = perfil.cargo || 'paciente'
  especialidade.value = perfil.especialidade || ''
  crmcrp.value = perfil.crmcrp || ''
  instituicao.value = perfil.instituicao || ''
  contatoEmergenciaNome.value = perfil.contatoEmergenciaNome || ''
  contatoEmergenciaRelacao.value = perfil.contatoEmergenciaRelacao || ''
  contatoEmergenciaTelefone.value = perfil.contatoEmergenciaTelefone || ''
  condicoesMedicas.value = perfil.condicoesMedicas || ''
  medicamentos.value = perfil.medicamentos || ''
  consentCompartilhar.value = Boolean(perfil.consentCompartilhar)
  preferenciasNotificacao.value = perfil.preferenciasNotificacao || { email: true, push: false }
  notasPrivadas.value = perfil.notasPrivadas || ''

  // Busca o documento no Firestore para preencher campos faltantes
  try {
    const docRef = doc(db, 'usuarios', perfil.uid)
    const snap = await getDoc(docRef)
    if (snap.exists()) {
      const data = snap.data()
      apelido.value = apelido.value || data.apelido || ''
      emailSecundario.value = emailSecundario.value || data.emailSecundario || ''
      telefone.value = telefone.value || data.telefone || ''
      dataNascimento.value = dataNascimento.value || data.dataNascimento || ''
      genero.value = genero.value || data.genero || ''
      endereco.value = endereco.value || data.endereco || ''
      cidade.value = cidade.value || data.cidade || ''
      estado.value = estado.value || data.estado || ''
      fusoHorario.value = fusoHorario.value || data.fusoHorario || ''
      locale.value = locale.value || data.locale || ''
      especialidade.value = especialidade.value || data.especialidade || ''
      instituicao.value = instituicao.value || data.instituicao || ''
      contatoEmergenciaNome.value = contatoEmergenciaNome.value || data.contatoEmergenciaNome || ''
      contatoEmergenciaRelacao.value = contatoEmergenciaRelacao.value || data.contatoEmergenciaRelacao || ''
      contatoEmergenciaTelefone.value = contatoEmergenciaTelefone.value || data.contatoEmergenciaTelefone || ''
      condicoesMedicas.value = condicoesMedicas.value || data.condicoesMedicas || ''
      medicamentos.value = medicamentos.value || data.medicamentos || ''
      consentCompartilhar.value = typeof data.consentCompartilhar === 'boolean' ? data.consentCompartilhar : consentCompartilhar.value
      preferenciasNotificacao.value = data.preferenciasNotificacao || preferenciasNotificacao.value
      notasPrivadas.value = notasPrivadas.value || data.notasPrivadas || ''
    }
  } catch (e) {
    console.error('Erro ao ler perfil do Firestore:', e)
  }
})

const salvar = async () => {
  erro.value = ''
  mensagem.value = ''

  const perfil = getCurrentUserProfile()
  if (!perfil) {
    router.push('/login')
    return
  }

  carregando.value = true

  try {
    const payload = {
      nome: nome.value.trim(),
      apelido: apelido.value.trim() || null,
      emailSecundario: emailSecundario.value.trim() || null,
      telefone: telefone.value.trim() || null,
      dataNascimento: dataNascimento.value || null,
      genero: genero.value || null,
      endereco: endereco.value.trim() || null,
      cidade: cidade.value.trim() || null,
      estado: estado.value.trim() || null,
      fusoHorario: fusoHorario.value || null,
      locale: locale.value || null,
      cargo: cargo.value,
      especialidade: especialidade.value.trim() || null,
      crmcrp: cargo.value === 'especialista' ? (crmcrp.value.trim() || null) : null,
      instituicao: instituicao.value.trim() || null,
      contatoEmergenciaNome: contatoEmergenciaNome.value.trim() || null,
      contatoEmergenciaRelacao: contatoEmergenciaRelacao.value.trim() || null,
      contatoEmergenciaTelefone: contatoEmergenciaTelefone.value.trim() || null,
      condicoesMedicas: condicoesMedicas.value.trim() || null,
      medicamentos: medicamentos.value.trim() || null,
      consentCompartilhar: Boolean(consentCompartilhar.value),
      preferenciasNotificacao: preferenciasNotificacao.value,
      notasPrivadas: notasPrivadas.value.trim() || null,
      updatedAtMs: Date.now(),
      updatedAtIso: new Date().toISOString(),
    }

    await setDoc(doc(db, 'usuarios', perfil.uid), payload, { merge: true })

    // Atualiza o sessionStorage com os novos dados
    const novoPerfil = { ...perfil, ...payload }
    sessionStorage.setItem('userProfile', JSON.stringify(novoPerfil))

    mensagem.value = 'Perfil atualizado com sucesso.'
    setTimeout(() => router.push('/profile'), 900)
  } catch (e) {
    console.error('Erro ao salvar perfil:', e)
    erro.value = e?.message || 'Nao foi possivel salvar o perfil.'
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 font-sans">
    <nav class="bg-white border-b border-slate-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16 items-center">
          <div class="flex items-center gap-3 cursor-pointer" @click="router.push('/')">
            <div class="bg-emerald-600 p-2 rounded-xl">
              <span class="text-white">🧠</span>
            </div>
            <span class="font-bold text-slate-800">Mente Ativa</span>
          </div>
        </div>
      </div>
    </nav>

    <main class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="bg-white rounded-2xl shadow-md p-8 border border-slate-200">
        <h1 class="text-2xl font-bold mb-4">Editar Perfil</h1>

        <form @submit.prevent="salvar" class="grid grid-cols-1 gap-4">
          <div v-if="erro" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{{ erro }}</div>
          <div v-if="mensagem" class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">{{ mensagem }}</div>

          <div>
            <label class="block text-sm font-semibold text-slate-700">Nome completo</label>
            <input v-model="nome" type="text" required class="mt-1 block w-full px-4 py-3 border rounded-xl" />
          </div>

          <div>
            <label class="block text-sm font-semibold text-slate-700">Nome preferido / Apelido</label>
            <input v-model="apelido" type="text" class="mt-1 block w-full px-4 py-3 border rounded-xl" />
          </div>

          <div>
            <label class="block text-sm font-semibold text-slate-700">E-mail</label>
            <input v-model="email" type="email" disabled class="mt-1 block w-full px-4 py-3 border rounded-xl bg-slate-50 text-slate-500" />
            <p class="text-xs text-slate-500 mt-1">Para alterar o e-mail reautentique-se via configuração de conta.</p>
          </div>

          <div>
            <label class="block text-sm font-semibold text-slate-700">E-mail secundário</label>
            <input v-model="emailSecundario" type="email" placeholder="contato@exemplo.com" class="mt-1 block w-full px-4 py-3 border rounded-xl" />
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-semibold text-slate-700">Telefone</label>
              <input v-model="telefone" type="tel" placeholder="(XX) XXXXX-XXXX" class="mt-1 block w-full px-4 py-3 border rounded-xl" />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-700">Data de nascimento</label>
              <input v-model="dataNascimento" type="date" class="mt-1 block w-full px-4 py-3 border rounded-xl" />
            </div>
          </div>

          <div>
            <label class="block text-sm font-semibold text-slate-700">Gênero</label>
            <select v-model="genero" class="mt-1 block w-full px-4 py-3 border rounded-xl bg-white">
              <option value="">Prefiro não informar</option>
              <option value="feminino">Feminino</option>
              <option value="masculino">Masculino</option>
              <option value="nao-binario">Não-binário</option>
              <option value="outro">Outro</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-semibold text-slate-700">Endereço</label>
            <input v-model="endereco" type="text" placeholder="Rua, número, complemento" class="mt-1 block w-full px-4 py-3 border rounded-xl" />
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-semibold text-slate-700">Cidade</label>
              <input v-model="cidade" type="text" class="mt-1 block w-full px-4 py-3 border rounded-xl" />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-700">Estado</label>
              <input v-model="estado" type="text" class="mt-1 block w-full px-4 py-3 border rounded-xl" />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-700">Fuso horário</label>
              <input v-model="fusoHorario" type="text" placeholder="America/Sao_Paulo" class="mt-1 block w-full px-4 py-3 border rounded-xl" />
            </div>
          </div>

          <div>
            <label class="block text-sm font-semibold text-slate-700">Locale / Idioma</label>
            <input v-model="locale" type="text" placeholder="pt-BR" class="mt-1 block w-full px-4 py-3 border rounded-xl" />
          </div>

          <div>
            <label class="block text-sm font-semibold text-slate-700">Função</label>
            <select v-model="cargo" class="mt-1 block w-full px-4 py-3 border rounded-xl bg-white">
              <option value="especialista">Especialista (Médico/Psicólogo)</option>
              <option value="responsavel">Responsável Familiar</option>
              <option value="administrador">Administrador</option>
              <option value="pesquisador">Pesquisador</option>
              <option value="paciente">Paciente</option>
              <option value="outro">Outro</option>
            </select>
          </div>

          <div v-if="cargo === 'especialista'">
            <label class="block text-sm font-semibold text-slate-700">Especialidade profissional</label>
            <input v-model="especialidade" type="text" class="mt-1 block w-full px-4 py-3 border rounded-xl" />

            <label class="block text-sm font-semibold text-slate-700 mt-4">Instituição / Clínica</label>
            <input v-model="instituicao" type="text" class="mt-1 block w-full px-4 py-3 border rounded-xl" />

            <label class="block text-sm font-semibold text-slate-700 mt-4">CRM / CRP</label>
            <input v-model="crmcrp" type="text" class="mt-1 block w-full px-4 py-3 border rounded-xl" />
          </div>

          <div class="mt-4">
            <h3 class="font-semibold text-slate-800">Contato de emergência</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
              <input v-model="contatoEmergenciaNome" placeholder="Nome" class="px-4 py-3 border rounded-xl" />
              <input v-model="contatoEmergenciaRelacao" placeholder="Relação" class="px-4 py-3 border rounded-xl" />
              <input v-model="contatoEmergenciaTelefone" placeholder="Telefone" class="px-4 py-3 border rounded-xl" />
            </div>
          </div>

          <div>
            <label class="block text-sm font-semibold text-slate-700">Condições médicas relevantes (resumo)</label>
            <textarea v-model="condicoesMedicas" rows="3" class="mt-1 block w-full px-4 py-3 border rounded-xl"></textarea>
          </div>

          <div>
            <label class="block text-sm font-semibold text-slate-700">Medicamentos em uso (resumo)</label>
            <textarea v-model="medicamentos" rows="2" class="mt-1 block w-full px-4 py-3 border rounded-xl"></textarea>
          </div>

          <div class="flex items-center gap-4">
            <label class="inline-flex items-center">
              <input type="checkbox" v-model="consentCompartilhar" class="mr-2" />
              <span>Autorizo compartilhar meus resultados com profissionais vinculados</span>
            </label>
          </div>

          <div class="mt-2">
            <p class="text-sm font-semibold text-slate-700 mb-2">Preferências de notificação</p>
            <label class="inline-flex items-center mr-4"><input type="checkbox" v-model="preferenciasNotificacao.email" class="mr-2" /> E-mail</label>
            <label class="inline-flex items-center"><input type="checkbox" v-model="preferenciasNotificacao.push" class="mr-2" /> Push</label>
          </div>

          <div>
            <label class="block text-sm font-semibold text-slate-700">Notas privadas</label>
            <textarea v-model="notasPrivadas" rows="3" class="mt-1 block w-full px-4 py-3 border rounded-xl"></textarea>
          </div>

          <!-- Vincular médico (apenas para pacientes) -->
          <div v-if="cargo === 'paciente'" class="mt-6 bg-slate-50 border border-slate-200 rounded-xl p-4">
            <h3 class="font-semibold text-slate-800 mb-2">Vincular Médico</h3>
            <p class="text-sm text-slate-600 mb-3">Pesquise e solicite vínculo com um profissional para que ele acesse seus resultados.</p>

            <div class="max-w-lg">
              <input v-model="doctorQuery" @input="onDoctorInput" placeholder="Digite o nome do médico..." class="w-full px-4 py-3 border rounded-xl" />

              <div v-if="searchingDoctors" class="mt-2 text-sm text-slate-500">Buscando...</div>

              <ul v-if="doctorSuggestions.length" class="mt-2 max-h-48 overflow-y-auto border rounded-xl bg-white">
                <li v-for="doc in doctorSuggestions" :key="doc.uid" class="px-3 py-2 hover:bg-slate-50 border-b last:border-b-0">
                  <div class="flex items-center justify-between">
                    <div>
                      <div class="font-medium">{{ doc.nome }}</div>
                      <div class="text-xs text-slate-500">{{ doc.instituicao || doc.crmcrp || doc.email }}</div>
                    </div>
                    <div>
                      <button @click.prevent="selectDoctorToLink(doc)" class="bg-emerald-600 text-white px-3 py-1 rounded-lg text-sm">Solicitar vínculo</button>
                    </div>
                  </div>
                </li>
              </ul>

              <p v-if="linkMessage" class="mt-2 text-sm text-emerald-700">{{ linkMessage }}</p>
            </div>
          </div>

          <div class="flex items-center gap-3 mt-4">
            <button :disabled="carregando" type="submit" class="bg-emerald-600 text-white px-6 py-3 rounded-xl font-bold disabled:opacity-50">{{ carregando ? 'Salvando...' : 'Salvar alterações' }}</button>
            <button type="button" @click="router.push('/profile')" class="px-6 py-3 rounded-xl border">Cancelar</button>
          </div>
        </form>
      </div>
    </main>
  </div>
</template>

<style scoped></style>

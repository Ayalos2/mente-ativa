<script setup>
import { useRouter } from 'vue-router'

// Inicializa o roteador para gerenciar a navegação entre as telas
const router = useRouter()

// Funções de navegação para os botões principais
const irParaTeste = () => {
  router.push('/teste/instrucoes')
}

const irParaLogin = () => {
  router.push('/login')
}

const irParaCadastro = () => {
  router.push('/cadastro')
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-emerald-200">
    
    <nav class="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-20 items-center">
          
          <div class="flex items-center gap-3 cursor-pointer" @click="router.push('/')">
            <div class="bg-emerald-600 p-2.5 rounded-xl shadow-md">
              <span class="text-white text-2xl" aria-hidden="true">🧠</span>
            </div>
            <span class="text-2xl font-bold text-slate-800 tracking-tight">Mente Ativa</span>
          </div>

          <div class="hidden md:flex items-center gap-8 text-base font-medium text-slate-600">
            <a href="#metodologia" class="hover:text-emerald-600 transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500 rounded-md px-2 py-1">Metodologia</a>
            <a href="#recursos" class="hover:text-emerald-600 transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500 rounded-md px-2 py-1">Recursos</a>
            <button @click="irParaLogin" class="bg-slate-100 px-6 py-2.5 rounded-full hover:bg-slate-200 transition-all font-bold text-slate-800 focus:ring-2 focus:ring-slate-400 outline-none">
              Login
            </button>
            <button @click="irParaCadastro" class="bg-emerald-600 text-white px-6 py-2.5 rounded-full hover:bg-emerald-700 transition-all font-bold focus:ring-2 focus:ring-emerald-500 outline-none">
              Cadastro
            </button>

          </div>

        </div>
      </div>
    </nav>

    <main class="relative overflow-hidden pt-16 pb-24 lg:pt-32">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        
        <div class="inline-flex items-center gap-2 bg-emerald-50 text-emerald-800 px-5 py-2 rounded-full text-sm font-bold mb-8 border border-emerald-200 shadow-sm">
          <span class="relative flex h-2.5 w-2.5">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          Plataforma de Saúde Digital
        </div>
        
        <h1 class="text-4xl md:text-6xl lg:text-7xl font-extrabold text-slate-900 leading-tight mb-6 tracking-tight">
          Monitoramento Cognitivo <br class="hidden md:block">
          <span class="text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 to-teal-500">Simples e Acessível</span>
        </h1>
        
        <p class="text-lg md:text-xl lg:text-2xl text-slate-600 max-w-3xl mx-auto mb-12 leading-relaxed">
          Auxiliando no diagnóstico precoce do Alzheimer através de testes digitais interativos e análise de dados em tempo real.
        </p>

        <div class="flex flex-col sm:flex-row gap-5 justify-center items-center">
          <button 
            @click="irParaTeste"
            class="w-full sm:w-auto bg-emerald-600 hover:bg-emerald-700 text-white px-12 py-5 rounded-2xl text-xl font-bold transition-all shadow-lg shadow-emerald-200 active:scale-95 focus:outline-none focus:ring-4 focus:ring-emerald-300"
            aria-label="Iniciar um novo teste cognitivo"
          >
            Iniciar Novo Teste
          </button>
          
          <button 
            @click="irParaPainelMedico"
            class="w-full sm:w-auto bg-white border-2 border-slate-200 text-slate-700 px-12 py-5 rounded-2xl text-xl font-bold hover:bg-slate-50 transition-all active:scale-95 focus:outline-none focus:ring-4 focus:ring-slate-200"
          >
            Painel Analítico
          </button>
        </div>
      </div>
    </main>

    <section id="recursos" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 border-t border-slate-200 bg-white">
      <div class="text-center mb-16">
        <h2 class="text-3xl md:text-4xl font-bold text-slate-900 mb-4">Como a plataforma funciona?</h2>
        <p class="text-lg text-slate-600">Extraímos dados clínicos de interações simples.</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-10 lg:gap-14">
        
        <div class="flex flex-col items-center text-center group p-6 rounded-3xl hover:bg-slate-50 transition-colors">
          <div class="w-20 h-20 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center text-4xl mb-6 group-hover:bg-blue-600 group-hover:text-white transition-all duration-300 shadow-sm">
            ⏱️
          </div>
          <h3 class="text-2xl font-bold mb-3 text-slate-800">Métricas de Precisão</h3>
          <p class="text-slate-600 leading-relaxed text-lg">
            Avaliamos o tempo de reação em milissegundos e os padrões de hesitação do paciente durante o teste.
          </p>
        </div>

        <div class="flex flex-col items-center text-center group p-6 rounded-3xl hover:bg-slate-50 transition-colors">
          <div class="w-20 h-20 bg-purple-50 text-purple-600 rounded-2xl flex items-center justify-center text-4xl mb-6 group-hover:bg-purple-600 group-hover:text-white transition-all duration-300 shadow-sm">
            🧠
          </div>
          <h3 class="text-2xl font-bold mb-3 text-slate-800">Inteligência Artificial</h3>
          <p class="text-slate-600 leading-relaxed text-lg">
            Modelos de Machine Learning classificam o nível de risco cognitivo processando o histórico do usuário.
          </p>
        </div>

        <div class="flex flex-col items-center text-center group p-6 rounded-3xl hover:bg-slate-50 transition-colors">
          <div class="w-20 h-20 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center text-4xl mb-6 group-hover:bg-emerald-600 group-hover:text-white transition-all duration-300 shadow-sm">
            👵
          </div>
          <h3 class="text-2xl font-bold mb-3 text-slate-800">Design Acessível</h3>
          <p class="text-slate-600 leading-relaxed text-lg">
            Interfaces de alto contraste, elementos amplos e ausência de ruído visual para não confundir o idoso.
          </p>
        </div>

      </div>
    </section>

    <footer class="bg-slate-900 py-12">
      <div class="max-w-7xl mx-auto px-4 text-center text-slate-400">
        <div class="flex justify-center items-center gap-2 mb-6 opacity-50">
          <span class="text-2xl">🧠</span>
          <span class="text-xl font-bold text-white tracking-tight">Mente Ativa</span>
        </div>
        <p class="font-medium">© 2026 Mente Ativa</p>
        <p class="mt-2 text-slate-500">TCC - Análise e Desenvolvimento de Sistemas</p>
      </div>
    </footer>

  </div>
</template>

<style scoped>
/* Transições suaves adicionais que o Tailwind não cobre por padrão */
button {
  -webkit-tap-highlight-color: transparent;
}
</style>
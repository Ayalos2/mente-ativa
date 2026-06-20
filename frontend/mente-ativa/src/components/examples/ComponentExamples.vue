<script setup>
import { ref } from 'vue'
import { AppButton, AppInput, AppCard, AppModal, AppToast, AppLoading, AppBadge } from '../base'

const showModal = ref(false)
const showToast = ref(false)
const toastType = ref('success')
const inputValue = ref('')
const inputError = ref('')
</script>

<template>
  <div class="min-h-screen bg-slate-50 p-8">
    <div class="max-w-4xl mx-auto space-y-8">
      
      <h1 class="text-3xl font-bold text-slate-900 mb-8">Exemplos de Componentes</h1>

      <!-- AppButton Examples -->
      <AppCard title="AppButton" subtitle="Botões com variantes e tamanhos">
        <div class="flex flex-wrap gap-4">
          <AppButton variant="primary">Primary</AppButton>
          <AppButton variant="secondary">Secondary</AppButton>
          <AppButton variant="danger">Danger</AppButton>
          <AppButton variant="ghost">Ghost</AppButton>
        </div>
        <div class="flex flex-wrap gap-4 mt-4">
          <AppButton variant="primary" size="sm">Small</AppButton>
          <AppButton variant="primary" size="md">Medium</AppButton>
          <AppButton variant="primary" size="lg">Large</AppButton>
        </div>
        <div class="mt-4">
          <AppButton variant="primary" :loading="true">Loading</AppButton>
        </div>
      </AppCard>

      <!-- AppInput Examples -->
      <AppCard title="AppInput" subtitle="Campos de entrada com validação">
        <div class="space-y-4 max-w-md">
          <AppInput 
            v-model="inputValue" 
            label="Nome" 
            placeholder="Digite seu nome"
            :error="inputError"
          />
          <AppInput 
            label="E-mail" 
            type="email" 
            placeholder="exemplo@email.com"
            required
          />
          <AppInput 
            label="Senha" 
            type="password" 
            placeholder="••••••••"
          />
        </div>
      </AppCard>

      <!-- AppBadge Examples -->
      <AppCard title="AppBadge" subtitle="Badges para status e categorias">
        <div class="flex flex-wrap gap-3">
          <AppBadge variant="default">Default</AppBadge>
          <AppBadge variant="success">Success</AppBadge>
          <AppBadge variant="warning">Warning</AppBadge>
          <AppBadge variant="info">Info</AppBadge>
          <AppBadge variant="emerald">Emerald</AppBadge>
          <AppBadge variant="amber">Amber</AppBadge>
          <AppBadge variant="violet">Violet</AppBadge>
        </div>
        <div class="flex flex-wrap gap-3 mt-4">
          <AppBadge variant="success" size="sm">Small</AppBadge>
          <AppBadge variant="success" size="md">Medium</AppBadge>
          <AppBadge variant="success" size="lg">Large</AppBadge>
        </div>
      </AppCard>

      <!-- AppModal Example -->
      <AppCard title="AppModal" subtitle="Modal com animações">
        <AppButton @click="showModal = true">Abrir Modal</AppButton>
        
        <AppModal :show="showModal" title="Exemplo de Modal" @close="showModal = false">
          <p class="text-slate-600 mb-4">Este é um exemplo de modal com animações suaves de entrada e saída.</p>
          <div class="flex justify-end gap-3">
            <AppButton variant="ghost" @click="showModal = false">Cancelar</AppButton>
            <AppButton variant="primary" @click="showModal = false">Confirmar</AppButton>
          </div>
        </AppModal>
      </AppCard>

      <!-- AppToast Example -->
      <AppCard title="AppToast" subtitle="Notificações toast">
        <div class="flex flex-wrap gap-3">
          <AppButton @click="() => { toastType = 'success'; showToast = true }">
            Success Toast
          </AppButton>
          <AppButton @click="() => { toastType = 'error'; showToast = true }">
            Error Toast
          </AppButton>
          <AppButton @click="() => { toastType = 'warning'; showToast = true }">
            Warning Toast
          </AppButton>
          <AppButton @click="() => { toastType = 'info'; showToast = true }">
            Info Toast
          </AppButton>
        </div>

        <AppToast
          :show="showToast"
          :type="toastType"
          :title="toastType === 'success' ? 'Sucesso!' : toastType === 'error' ? 'Erro!' : toastType === 'warning' ? 'Aviso!' : 'Informação'"
          message="Esta é uma mensagem de notificação toast."
          @close="showToast = false"
        />
      </AppCard>

      <!-- AppLoading Example -->
      <AppCard title="AppLoading" subtitle="Indicadores de carregamento">
        <div class="flex flex-wrap gap-6 items-center">
          <AppLoading size="sm" text="Pequeno" />
          <AppLoading size="md" text="Médio" />
          <AppLoading size="lg" text="Grande" />
        </div>
      </AppCard>

    </div>
  </div>
</template>
<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  },
  loadingText: {
    type: String,
    default: 'Carregando...'
  }
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-emerald-200">
    
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-24">
      <AppLoading :text="loadingText" size="lg" />
    </div>

    <!-- Content -->
    <div v-else class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <!-- Page Header -->
      <div v-if="title" class="mb-8">
        <h1 class="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight">{{ title }}</h1>
        <p v-if="subtitle" class="text-lg text-slate-600 mt-2">{{ subtitle }}</p>
      </div>
      
      <slot />
    </div>
  </div>
</template>
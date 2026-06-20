<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppNavbar from './AppNavbar.vue'

const route = useRoute()

const showNavbar = computed(() => {
  return !['/login', '/cadastro'].includes(route.path)
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 font-sans text-slate-900">
    <AppNavbar v-if="showNavbar" />
    <main>
      <slot />
    </main>
  </div>
</template>
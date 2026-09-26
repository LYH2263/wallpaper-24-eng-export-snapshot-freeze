<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const walls = ref([])
onMounted(async () => { walls.value = (await getJSON('/api/walls')).items })
</script>
<template>
  <div class="page"><h1>条带总览</h1>
  <ul><li v-for="w in walls" :key="w.id">{{ w.name }} · 周长 {{ w.perimeter }}m · {{ w.data_quality }}</li></ul></div>
</template>

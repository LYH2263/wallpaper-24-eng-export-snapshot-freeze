<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => { items.value = (await getJSON('/api/walls')).items })
</script>
<template>
  <div class="page"><h1>墙面列表</h1>
  <table><tr v-for="w in items" :key="w.id"><td>{{ w.name }}</td><td>{{ w.perimeter }}m</td><td><router-link :to="`/walls/${w.id}`">详情</router-link></td></tr></table>
  </div>
</template>

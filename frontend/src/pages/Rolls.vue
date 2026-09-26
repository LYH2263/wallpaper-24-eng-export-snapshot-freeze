<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => { items.value = (await getJSON('/api/rolls')).items })
</script>
<template>
  <div class="page"><h1>纸卷规格</h1>
  <div v-for="r in items" :key="r.id" class="roll-chip">{{ r.name }} · 宽{{ r.width }} · 长{{ r.length }} · 花距{{ r.pattern_cm }}cm</div>
  </div>
</template>

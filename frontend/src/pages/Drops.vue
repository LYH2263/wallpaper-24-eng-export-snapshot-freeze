<script setup>
import { ref } from 'vue'
import DropStripBar from '../components/DropStripBar.vue'
const demo = ref({ drops: 12, dropLen: 2.7, rolls: 4 })
</script>
<template>
  <div class="page"><h1>裁条预览</h1><DropStripBar v-bind="demo" /></div>
</template>

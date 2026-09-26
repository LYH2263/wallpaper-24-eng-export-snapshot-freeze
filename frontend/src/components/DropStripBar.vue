<script setup>
defineProps({ drops: Number, dropLen: Number, rolls: Number })
</script>
<template>
  <div class="strip-bar">
    <div v-for="n in Math.min(drops || 0, 24)" :key="n" class="strip" :style="{ height: `${Math.min(120, (dropLen || 2) * 30)}px` }"></div>
    <p>共 {{ drops }} 条，约 {{ rolls }} 卷</p>
  </div>
</template>

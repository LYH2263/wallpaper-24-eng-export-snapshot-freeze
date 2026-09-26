<template>
  <div class="wp-frame">
    <header class="wp-header">
      <span class="logo">墙纸卷数</span>
      <nav>
        <router-link to="/">条带总览</router-link>
        <router-link to="/walls">墙面</router-link>
        <router-link to="/rolls">纸卷</router-link>
        <router-link to="/drops">裁条预览</router-link>
        <router-link to="/bench">算卷</router-link>
        <router-link to="/pattern">对花说明</router-link>
        <router-link to="/history">记录</router-link>
        <router-link to="/settings">设置</router-link>
      </nav>
    </header>
    <router-view />
  </div>
</template>

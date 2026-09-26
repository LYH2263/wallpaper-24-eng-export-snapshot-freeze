import { createRouter, createWebHistory } from 'vue-router'
import Overview from './pages/Overview.vue'
import Walls from './pages/Walls.vue'
import WallDetail from './pages/WallDetail.vue'
import Rolls from './pages/Rolls.vue'
import Drops from './pages/Drops.vue'
import Bench from './pages/Bench.vue'
import Pattern from './pages/Pattern.vue'
import History from './pages/History.vue'
import Settings from './pages/Settings.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Overview },
    { path: '/walls', component: Walls },
    { path: '/walls/:id', component: WallDetail, props: true },
    { path: '/rolls', component: Rolls },
    { path: '/drops', component: Drops },
    { path: '/bench', component: Bench },
    { path: '/pattern', component: Pattern },
    { path: '/history', component: History },
    { path: '/settings', component: Settings },
  ],
})

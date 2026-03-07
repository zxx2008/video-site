import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('../views/HomeView.vue') },
  { path: '/upload', name: 'upload', component: () => import('../views/UploadView.vue') },
  { path: '/video/:id', name: 'video', component: () => import('../views/VideoView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

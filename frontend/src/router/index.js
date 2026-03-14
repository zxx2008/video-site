import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('../views/HomeView.vue') },
  { path: '/upload', name: 'upload', component: () => import('../views/UploadView.vue') },
  { path: '/video/:id', name: 'video', component: () => import('../views/VideoView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // 如果是从视频详情页返回到主页，让主页组件自己处理滚动恢复
    if (to.path === '/' && from.path.startsWith('/video/')) {
      return false // 返回 false 表示不执行默认滚动行为
    }
    // 其他情况使用默认行为
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0 }
  },
})

export default router

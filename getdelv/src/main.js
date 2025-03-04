import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './assets/main.css'
import Home from './components/Home.vue'
import Pitch from './components/Pitch.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Home },
    { path: '/pitch', component: Pitch }
  ]
})

const app = createApp(App)
app.use(router)
app.mount('#app')
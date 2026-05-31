import './assets/main.css'

import { createApp, nextTick } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import translate from 'i18n-jsautotranslate'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

window.translate = translate

nextTick(() => {
  translate.language.setLocal('chinese_simplified')
  translate.service.use('client.edge')
  translate.selectLanguageTag.show = false
  translate.listener.start()
  translate.execute()
})

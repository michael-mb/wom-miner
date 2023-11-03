// Template JS
import './assets/js/jquery-3.6.0.min'
import './assets/js/bootstrap.bundle.min.js'
import './assets/js/feather.min.js'
import './assets/plugins/slimscroll/jquery.slimscroll.min.js'
import './assets/js/script.js'

// Template CSS
import './assets/main.css'
import './assets/css/bootstrap.min.css'
import './assets/plugins/fontawesome/css/fontawesome.min.css'
import './assets/css/feather.css'
import './assets/plugins/fontawesome/css/all.min.css'
import './assets/css/style.css'

// Vue
import VueBlocksTree from 'vue3-blocks-tree';
import 'vue3-blocks-tree/dist/vue3-blocks-tree.css';

import {createApp, defineAsyncComponent} from 'vue'
import { createPinia } from 'pinia'
import router from './router'

let defaultOptions = {treeName:'blocks-tree'}
createApp(defineAsyncComponent(() => import('./App.vue')))
    .use(createPinia())
    .use(router)
    .use(VueBlocksTree,defaultOptions)
    .mount('#app');
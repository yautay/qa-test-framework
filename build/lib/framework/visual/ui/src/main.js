import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import { initTheme } from "./lib/themes";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import bootstrap from "bootstrap/dist/js/bootstrap.bundle.min.js";

const pinia = createPinia();

initTheme();
const app = createApp(App);
app.config.devtools = true;
app.use(pinia);

app.mount("#app");

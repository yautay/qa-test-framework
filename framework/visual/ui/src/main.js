import { createApp } from "vue";
import App from "./App.vue";
import { initTheme } from "./lib/themes";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

initTheme();
createApp(App).mount("#app");

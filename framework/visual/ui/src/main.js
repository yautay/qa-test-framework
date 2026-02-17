import { createApp } from "vue";
import App from "./App.vue";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

const scriptEl = document.getElementById("vrt-results");
const raw = scriptEl?.textContent?.trim();
const inlineResults = raw && raw !== "__VRT_INLINE_RESULTS__" ? JSON.parse(raw) : { results: [] };
window.__VRT_RESULTS__ = inlineResults;

createApp(App).mount("#app");

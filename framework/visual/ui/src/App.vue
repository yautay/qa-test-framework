<template>
  <div class="app-wrapper">
    <div class="container-fluid p-3">
      <HeroPage v-if="route.page === 'hero'" />
      <ReportPage v-else :run-id="route.runId" />
    </div>
  </div>
</template>

<script>
import HeroPage from "./pages/HeroPage.vue";
import ReportPage from "./pages/ReportPage.vue";
import { parseRuntimeRoute } from "./lib/runtimeRoute";

export default {
  name: "VisualUiApp",
  components: {
    HeroPage,
    ReportPage,
  },
  data() {
    return {
      route: parseRuntimeRoute(window.location.pathname),
    };
  },
  methods: {
    handlePopState() {
      this.route = parseRuntimeRoute(window.location.pathname);
    },
  },
  mounted() {
    window.addEventListener("popstate", this.handlePopState);
  },
  beforeUnmount() {
    window.removeEventListener("popstate", this.handlePopState);
  },
};
</script>

<style>
:root {
  --primary: #0d6efd;
  --secondary: #6c757d;
  --success: #198754;
  --danger: #dc3545;
  --warning: #ffc107;
  --body-bg: #ffffff;
  --body-color: #212529;
  --card-bg: #ffffff;
  --border: rgba(0, 0, 0, 0.08);
  --text-muted: #6c757d;
  --hero-gradient: linear-gradient(135deg, #f3f9ff 0%, #e8f5e9 100%);
}

[data-theme="dark"] {
  --primary: #6ea8fe;
  --secondary: #6c757d;
  --success: #75b798;
  --danger: #ea868f;
  --warning: #ffda6a;
  --body-bg: #212529;
  --body-color: #f8f9fa;
  --card-bg: #343a40;
  --border: rgba(255, 255, 255, 0.08);
  --text-muted: #adb5bd;
  --hero-gradient: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
}

[data-theme="dracula"] {
  --primary: #bd93f9;
  --secondary: #6272a4;
  --success: #50fa7b;
  --danger: #ff5555;
  --warning: #f1fa8c;
  --body-bg: #282a36;
  --body-color: #f8f8f2;
  --card-bg: #383a4e;
  --border: rgba(255, 255, 255, 0.1);
  --text-muted: #6272a4;
  --hero-gradient: linear-gradient(135deg, #44475a 0%, #282a36 100%);
}

[data-theme="gruvbox"] {
  --primary: #83a598;
  --secondary: #928374;
  --success: #b8bb26;
  --danger: #fb4934;
  --warning: #fabd2f;
  --body-bg: #282828;
  --body-color: #ebdbb2;
  --card-bg: #3c3836;
  --border: rgba(255, 255, 255, 0.1);
  --text-muted: #a89984;
  --hero-gradient: linear-gradient(135deg, #3c3836 0%, #282828 100%);
}

[data-theme="atom"] {
  --primary: #61afef;
  --secondary: #5c6370;
  --success: #98c379;
  --danger: #e06c75;
  --warning: #e5c07b;
  --body-bg: #282c34;
  --body-color: #abb2bf;
  --card-bg: #21252b;
  --border: rgba(255, 255, 255, 0.1);
  --text-muted: #5c6370;
  --hero-gradient: linear-gradient(135deg, #21252b 0%, #282c34 100%);
}

body {
  background-color: var(--body-bg);
  color: var(--body-color);
  min-height: 100vh;
}

.app-wrapper {
  min-height: 100vh;
  background-color: var(--body-bg);
}

.container-fluid {
  background-color: var(--body-bg);
  color: var(--body-color);
  min-height: 100vh;
}

.card {
  background-color: var(--card-bg);
  border-color: var(--border);
  color: var(--body-color);
}

.card-body {
  color: var(--body-color);
}

.text-muted {
  color: var(--text-muted) !important;
}

.btn-primary {
  background-color: var(--primary);
  border-color: var(--primary);
}

.btn-primary:hover {
  background-color: var(--primary);
  opacity: 0.9;
}

.form-control {
  background-color: var(--card-bg);
  border-color: var(--border);
  color: var(--body-color);
}

.form-control:focus {
  background-color: var(--card-bg);
  color: var(--body-color);
}

.form-control::placeholder {
  color: var(--text-muted);
}

.form-select {
  background-color: var(--card-bg);
  border-color: var(--border);
  color: var(--body-color);
}

.badge {
  color: var(--body-color);
}

.modal-content {
  background-color: var(--card-bg);
  color: var(--body-color);
  border-color: var(--border);
}

.modal-header {
  background-color: var(--card-bg);
  border-color: var(--border);
}

.modal-body {
  background-color: var(--card-bg);
  color: var(--body-color);
}

.modal-footer {
  background-color: var(--card-bg);
  border-color: var(--border);
}

.table {
  --bs-table-bg: var(--card-bg);
  color: var(--body-color);
}

.table-light {
  --bs-table-bg: var(--body-bg);
  color: var(--body-color);
}

.table-hover tbody tr:hover {
  --bs-table-hover-bg: var(--body-bg);
}

.table-active {
  background-color: var(--body-bg) !important;
}

.btn-close {
  filter: invert(1) grayscale(100%) brightness(200%);
}

[data-theme="bootstrap"] .btn-close {
  filter: none;
}
</style>

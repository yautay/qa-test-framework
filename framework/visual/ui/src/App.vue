<template>
  <div class="app-wrapper">
    <div class="container-fluid p-3">
      <HeroPage v-if="route.page === 'hero'" />
      <ReportPage v-else :run-id="route.runId" :key="route.runId" />
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
  --on-primary: #ffffff;
  --on-secondary: #ffffff;
  --on-success: #ffffff;
  --on-danger: #ffffff;
  --on-warning: #212529;
  --body-bg: #ffffff;
  --body-color: #212529;
  --hero-text: #212529;
  --hero-muted: #495057;
  --card-bg: #ffffff;
  --border: rgba(0, 0, 0, 0.08);
  --text-muted: #6c757d;
  --hero-gradient: linear-gradient(135deg, #f3f9ff 0%, #e8f5e9 100%);
  --dropdown-gradient: linear-gradient(135deg, #e8f4fd 0%, #f5f5f5 100%);
  --success-subtle: #d1e7dd;
  --danger-subtle: #f8d7da;
  --warning-subtle: #fff3cd;
  --success-emphasis: #0f5132;
  --danger-emphasis: #842029;
  --warning-emphasis: #664d03;
  --report-excluded-border: #ffc107;
  --report-excluded-text: #664d03;
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
  --dropdown-gradient: linear-gradient(135deg, #3a3f47 0%, #2d3238 100%);
  --success-subtle: #1f3a2e;
  --danger-subtle: #3d1f20;
  --warning-subtle: #3d3300;
  --success-emphasis: #75b798;
  --danger-emphasis: #ea868f;
  --warning-emphasis: #ffda6a;
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
  --dropdown-gradient: linear-gradient(135deg, #44475a 0%, #383a4e 100%);
  --success-subtle: #1a3b26;
  --danger-subtle: #3b1f20;
  --warning-subtle: #3b3616;
  --success-emphasis: #50fa7b;
  --danger-emphasis: #ff5555;
  --warning-emphasis: #f1fa8c;
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
  --dropdown-gradient: linear-gradient(135deg, #45403b 0%, #3c3836 100%);
  --success-subtle: #2d3612;
  --danger-subtle: #3b1210;
  --warning-subtle: #3b3610;
  --success-emphasis: #b8bb26;
  --danger-emphasis: #fb4934;
  --warning-emphasis: #fabd2f;
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
  --dropdown-gradient: linear-gradient(135deg, #2c313a 0%, #21252b 100%);
  --success-subtle: #243324;
  --danger-subtle: #3b2429;
  --warning-subtle: #3b3624;
  --success-emphasis: #98c379;
  --danger-emphasis: #e06c75;
  --warning-emphasis: #e5c07b;
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
  color: var(--on-primary);
}

.btn-primary:hover {
  background-color: var(--primary);
  opacity: 0.9;
}

.btn-success {
  background-color: var(--success);
  border-color: var(--success);
  color: var(--on-success);
}

.btn-danger {
  color: var(--on-danger);
}

.btn-warning {
  color: var(--on-warning);
}

.btn-outline-primary {
  --bs-btn-border-color: var(--primary);
  --bs-btn-color: var(--primary);
  color: var(--primary);
  border-color: var(--primary);
}

.btn-outline-primary:hover {
  background-color: var(--primary);
  border-color: var(--primary);
}

.btn-outline-secondary {
  --bs-btn-border-color: var(--secondary);
  --bs-btn-color: var(--secondary);
  color: var(--secondary);
  border-color: var(--secondary);
}

.btn-outline-secondary:hover {
  background-color: var(--secondary);
  border-color: var(--secondary);
}

.btn-outline-success {
  --bs-btn-border-color: var(--success);
  --bs-btn-color: var(--success);
  color: var(--success);
  border-color: var(--success);
}

.btn-outline-success:hover {
  background-color: var(--success);
  border-color: var(--success);
}

.btn-outline-danger {
  --bs-btn-border-color: var(--danger);
  --bs-btn-color: var(--danger);
  color: var(--danger);
  border-color: var(--danger);
}

.btn-outline-danger:hover {
  background-color: var(--danger);
  border-color: var(--danger);
}

.btn-outline-warning {
  --bs-btn-border-color: var(--warning);
  --bs-btn-color: var(--warning);
  color: var(--warning);
  border-color: var(--warning);
}

.btn-outline-warning:hover {
  background-color: var(--warning);
  border-color: var(--warning);
  color: var(--on-warning);
}

.bg-success-subtle {
  background-color: var(--success-subtle) !important;
}

.bg-danger-subtle {
  background-color: var(--danger-subtle) !important;
}

.bg-warning-subtle {
  background-color: var(--warning-subtle) !important;
}

.text-success-emphasis {
  color: var(--success-emphasis) !important;
}

.text-danger-emphasis {
  color: var(--danger-emphasis) !important;
}

.text-warning-emphasis {
  color: var(--warning-emphasis) !important;
}

.text-dark {
  color: var(--body-color) !important;
}

.text-success {
  color: var(--success) !important;
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

.bg-primary,
.text-bg-primary {
  color: var(--on-primary) !important;
}

.bg-secondary,
.text-bg-secondary {
  color: var(--on-secondary) !important;
}

.bg-success,
.text-bg-success {
  color: var(--on-success) !important;
}

.bg-danger,
.text-bg-danger {
  color: var(--on-danger) !important;
}

.bg-warning,
.text-bg-warning {
  color: var(--on-warning) !important;
}

[data-theme="dark"] .btn-close,
[data-theme="dracula"] .btn-close,
[data-theme="gruvbox"] .btn-close,
[data-theme="atom"] .btn-close {
  filter: invert(1) grayscale(100%) brightness(200%);
}
</style>

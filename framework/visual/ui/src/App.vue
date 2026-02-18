<template>
  <div class="container-fluid p-3">
    <HeroPage v-if="route.page === 'hero'" />
    <ReportPage v-else :run-id="route.runId" />
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
};
</script>

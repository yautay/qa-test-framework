<template>
  <section class="hero-wrap">
    <AppHeader />
    <HeroHeader :total="store.filteredReports.length" />
    <ReportsFilters />
    <ReportsList :reports="store.filteredReports" />
  </section>
</template>

<script setup>
import { onMounted, onBeforeUnmount } from "vue";
import AppHeader from "../components/AppHeader.vue";
import HeroHeader from "../components/hero/HeroHeader.vue";
import ReportsFilters from "../components/hero/ReportsFilters.vue";
import ReportsList from "../components/hero/ReportsList.vue";
import { useReportsStore } from "../stores/reportsStore";

const store = useReportsStore();

onMounted(async () => {
  await store.fetchReports();
  store.startAutoRefresh();
});

onBeforeUnmount(() => {
  store.stopAutoRefresh();
});
</script>

<style scoped>
.hero-wrap {
  max-width: 96%;
  margin: 0 auto;
}
</style>

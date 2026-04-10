<template>
  <section class="hero-wrap">
    <AppHeader />
    <HeroHeader :total="store.filteredReports.length" />
    <ReportsFilters />
    <ReportsList :reports="store.filteredReports" @send-jira="openModal" />
    <JiraSendModal
      :visible="modalVisible"
      :report="selectedReport"
      :default-ticket="defaultTicket"
      :default-note="defaultNote"
      :default-username="defaultUsername"
      :default-password="defaultPassword"
      :default-mode="defaultMode"
      :auth-mode="jiraConfig.auth_mode"
      :auth-configured="jiraConfig.auth_configured"
      :error-message="errorMessage"
      :is-submitting="isSubmitting"
      @submit="handleSendJira"
      @cancel="closeModal"
    />
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { t } from "../lib/i18n";
import AppHeader from "../components/AppHeader.vue";
import HeroHeader from "../components/hero/HeroHeader.vue";
import ReportsFilters from "../components/hero/ReportsFilters.vue";
import ReportsList from "../components/hero/ReportsList.vue";
import JiraSendModal from "../components/hero/JiraSendModal.vue";
import { fetchAppInfo, sendJiraComment } from "../lib/api/reportsApi";
import { useReportsStore } from "../stores/reportsStore";

const store = useReportsStore();
const appInfo = ref(null);
const modalVisible = ref(false);
const selectedReport = ref(null);
const isSubmitting = ref(false);
const errorMessage = ref("");

const jiraConfig = computed(() => appInfo.value?.ui_config?.jira || {});
const defaultTicket = computed(() => (jiraConfig.value.default_ticket || "").trim());
const defaultNote = computed(() => String(jiraConfig.value.default_note || ""));
const defaultUsername = computed(() => String(jiraConfig.value.default_username || ""));
const defaultPassword = computed(() => String(jiraConfig.value.default_password || ""));
const defaultMode = computed(() => String(jiraConfig.value.default_mode || "auto"));

const openModal = (report) => {
  selectedReport.value = report;
  errorMessage.value = "";
  modalVisible.value = true;
};

const closeModal = () => {
  modalVisible.value = false;
  selectedReport.value = null;
};

const handleSendJira = async (payload) => {
  if (!selectedReport.value) {
    errorMessage.value = t("jira.errors.noReport");
    return;
  }
  isSubmitting.value = true;
  errorMessage.value = "";
  try {
    const body = {
      jira_ticket: payload.ticket.toUpperCase(),
      user_note: payload.note,
      mode: String(payload.mode || "auto"),
    };
    if (payload.auth) {
      body.auth = payload.auth;
    }
    await sendJiraComment(selectedReport.value.run_id, body);
    await store.fetchReports();
    closeModal();
  } catch (error) {
    errorMessage.value = error?.message || t("jira.errors.unexpected");
  } finally {
    isSubmitting.value = false;
  }
};

const loadAppInfo = async () => {
  try {
    appInfo.value = await fetchAppInfo();
  } catch (error) {
    console.warn("failed to load app info", error);
  }
};

onMounted(async () => {
  await Promise.all([store.fetchReports(), loadAppInfo()]);
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

import { ref } from 'vue';

const alerts = ref([]);

export function useSyncAlerts() {
  function showToast(message, type = 'warning', duration = 5000) {
    const id = Date.now();
    alerts.value.push({ id, message, type });
    setTimeout(() => dismissToast(id), duration);
  }

  function dismissToast(id) {
    alerts.value = alerts.value.filter((a) => a.id !== id);
  }

  function clearAll() {
    alerts.value = [];
  }

  return { alerts, showToast, dismissToast, clearAll };
}

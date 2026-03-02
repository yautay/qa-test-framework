<template>
  <div class="toast-container position-fixed bottom-0 end-0 p-3" style="z-index: 9999;">
    <div
      v-for="alert in alerts"
      :key="alert.id"
      class="toast show"
      :class="alertClass(alert.type)"
      role="alert"
    >
      <div class="toast-body d-flex justify-content-between align-items-center text-white">
        <span>{{ alert.message }}</span>
        <button
          type="button"
          class="btn-close btn-close-white ms-2"
          @click="dismissToast(alert.id)"
        ></button>
      </div>
    </div>
  </div>
</template>

<script>
import { useSyncAlerts } from '../composables/useSyncAlerts';

export default {
  name: 'SyncToasts',
  setup() {
    const { alerts, dismissToast } = useSyncAlerts();

    function alertClass(type) {
      const classes = {
        warning: 'bg-warning',
        error: 'bg-danger',
        success: 'bg-success',
        info: 'bg-info',
      };
      return classes[type] || 'bg-warning';
    }

    return {
      alerts,
      dismissToast,
      alertClass,
    };
  },
};
</script>

<style scoped>
.toast-container {
  pointer-events: none;
}
.toast {
  pointer-events: auto;
  min-width: 280px;
  margin-top: 0.5rem;
}
</style>

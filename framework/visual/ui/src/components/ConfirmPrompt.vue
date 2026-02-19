<template>
  <div v-if="active && type === 'send-report'" class="global-prompt-overlay">
    <div class="global-prompt-card">
      <div class="global-prompt-title">{{ t('prompt.confirm') }}</div>
      <div class="global-prompt-text">{{ t('report.confirmSend') }}</div>
      <div class="global-prompt-hints">{{ t('prompt.shiftNo') }} &nbsp;•&nbsp; {{ t('prompt.spaceYes') }}</div>
      <div class="global-prompt-actions">
        <button type="button" class="btn btn-sm btn-primary" @click="$emit('confirm')">{{ t('prompt.yes') }}</button>
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="$emit('cancel')">{{ t('prompt.no') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { t } from "../lib/i18n";

defineProps({
  active: {
    type: Boolean,
    default: false,
  },
  type: {
    type: String,
    default: null,
  },
});

defineEmits(["confirm", "cancel"]);
</script>

<style scoped>
.global-prompt-overlay {
  position: fixed;
  inset: 0;
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
}

.global-prompt-card {
  width: 100%;
  max-width: 360px;
  background: var(--card-bg);
  border-radius: 0.75rem;
  box-shadow: 0 20px 45px rgba(0, 0, 0, 0.2);
  padding: 1.25rem 1.5rem;
  text-align: center;
}

.global-prompt-title {
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.global-prompt-text {
  margin-bottom: 0.5rem;
}

.global-prompt-hints {
  color: var(--text-muted);
  font-size: 0.85rem;
}

.global-prompt-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 0.75rem;
}
</style>

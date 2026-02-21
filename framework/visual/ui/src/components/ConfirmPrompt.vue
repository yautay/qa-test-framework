<template>
  <teleport v-if="active && isModalPrompt" to="#vrtModal .modal-content">
    <div class="global-prompt-overlay in-modal">
      <div v-if="type === 'bug' || type === 'aso'" class="global-prompt-card">
        <div class="global-prompt-title">{{ t('prompt.confirm') }}</div>
        <div class="global-prompt-text">{{ t('prompt.areYouSure') }} {{ t('tags.' + type) }}?</div>
        <div v-if="isTagPrompt" class="prompt-note">
          <textarea
            ref="noteInput"
            class="form-control prompt-textarea"
            :value="note"
            :maxlength="noteMaxLength"
            :placeholder="t('prompt.notePlaceholder')"
            @input="$emit('note-input', $event.target.value)"
          ></textarea>
          <div class="prompt-counter">{{ noteLength }}/{{ noteMaxLength }}</div>
        </div>
        <div class="global-prompt-actions">
          <button type="button" class="btn btn-sm btn-primary" @click="$emit('confirm')">{{ t('prompt.yes') }}</button>
          <button type="button" class="btn btn-sm btn-outline-secondary" @click="$emit('cancel')">{{ t('prompt.no') }}</button>
        </div>
      </div>

      <div v-else-if="isRemoveType" class="global-prompt-card">
        <div class="global-prompt-title">{{ t('prompt.confirm') }}</div>
        <div class="global-prompt-text">{{ t('prompt.removeTag') }} {{ t('tags.' + removeType) }}?</div>
        <div class="global-prompt-hints">{{ t('prompt.shiftNo') }} &nbsp;•&nbsp; {{ t('prompt.spaceYes') }}</div>
        <div class="global-prompt-actions">
          <button type="button" class="btn btn-sm btn-primary" @click="$emit('confirm')">{{ t('prompt.yes') }}</button>
          <button type="button" class="btn btn-sm btn-outline-secondary" @click="$emit('cancel')">{{ t('prompt.no') }}</button>
        </div>
      </div>
    </div>
  </teleport>

  <div v-else-if="active" class="global-prompt-overlay">
    <div v-if="type === 'send-report'" class="global-prompt-card">
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
import { computed, nextTick, ref, watch } from "vue";
import { t } from "../lib/i18n";

const props = defineProps({
  active: {
    type: Boolean,
    default: false,
  },
  type: {
    type: String,
    default: null,
  },
  note: {
    type: String,
    default: "",
  },
  noteMaxLength: {
    type: Number,
    default: 500,
  },
});

defineEmits(["confirm", "cancel", "note-input"]);

const isRemoveType = computed(() => {
  return props.type && props.type.startsWith("remove-");
});

const isTagPrompt = computed(() => {
  return props.type === "bug" || props.type === "aso";
});

const noteLength = computed(() => {
  return (props.note || "").length;
});

const isModalPrompt = computed(() => {
  return props.type === "bug" || props.type === "aso" || isRemoveType.value;
});

const noteInput = ref(null);

watch(
  () => [props.active, props.type],
  async ([active, type]) => {
    if (!active || (type !== "bug" && type !== "aso")) return;
    await nextTick();
    noteInput.value?.focus();
  }
);

const removeType = computed(() => {
  if (isRemoveType.value) {
    return props.type.replace("remove-", "");
  }
  return "";
});
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

.global-prompt-overlay.in-modal {
  position: absolute;
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

.prompt-note {
  margin: 0.65rem 0 0.5rem;
  text-align: left;
}

.prompt-textarea {
  min-height: 90px;
  resize: vertical;
  background: var(--card-bg);
  color: var(--body-color);
  border-color: var(--border);
}

.prompt-textarea:focus {
  background: var(--card-bg);
  color: var(--body-color);
  border-color: var(--primary);
}

.prompt-counter {
  margin-top: 0.35rem;
  color: var(--text-muted);
  font-size: 0.75rem;
  text-align: right;
}

.global-prompt-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 0.75rem;
}
</style>

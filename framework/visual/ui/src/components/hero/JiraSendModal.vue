<template>
  <teleport to="body">
    <div v-if="visible" class="jira-modal-overlay">
      <div class="jira-modal-card">
        <header class="jira-modal-header">
          <h3 class="jira-modal-title">{{ t('jira.modalTitle') }}</h3>
          <button type="button" class="btn-close" @click="emitCancel" :disabled="isSubmitting" aria-label="Close"></button>
        </header>

        <div v-if="isSubmitting" class="progress mb-3">
          <div
            class="progress-bar progress-bar-striped progress-bar-animated"
            role="progressbar"
            style="width: 100%"
          >
            {{ t('jira.progress') }}
          </div>
        </div>

        <form class="jira-modal-body" @submit.prevent="handleSubmit">
          <div class="mb-3">
            <label class="form-label" for="jira-ticket">{{ t('jira.ticketLabel') }}</label>
            <input
              id="jira-ticket"
              class="form-control"
              type="text"
              v-model="ticketInput"
              :disabled="isSubmitting"
              :placeholder="t('jira.ticketPlaceholder')"
            />
            <div v-if="ticketInput && !ticketValid" class="form-text text-danger">
              {{ t('jira.ticketInvalid') }}
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label" for="jira-note">{{ t('jira.noteLabel') }}</label>
            <textarea
              id="jira-note"
              class="form-control"
              rows="3"
              v-model="noteDraft"
              :disabled="isSubmitting"
              :placeholder="t('jira.notePlaceholder')"
            ></textarea>
          </div>

          <div class="mb-3">
            <label class="form-label" for="jira-mode">{{ t('jira.modeLabel') }}</label>
            <select
              id="jira-mode"
              class="form-select"
              v-model="modeInput"
              :disabled="isSubmitting"
            >
              <option value="auto">{{ t('jira.modeAuto') }}</option>
              <option value="comment">{{ t('jira.modeComment') }}</option>
              <option value="subtask">{{ t('jira.modeSubtask') }}</option>
            </select>
          </div>

          <div v-if="!authConfigured" class="mb-3">
            <div class="jira-auth-title">{{ t('jira.authTitle') }}</div>
            <p class="jira-auth-hint">{{ t('jira.authHint') }}</p>
            <div v-if="authMode === 'token'" class="mb-2">
              <label class="form-label" for="jira-token">{{ t('jira.authToken') }}</label>
              <input
                id="jira-token"
                class="form-control"
                type="text"
                v-model="authToken"
                :disabled="isSubmitting"
              />
            </div>
            <div v-else>
              <div class="mb-2">
                <label class="form-label" for="jira-username">{{ t('jira.authUsername') }}</label>
                <input
                  id="jira-username"
                  class="form-control"
                  type="text"
                  v-model="authUsername"
                  :disabled="isSubmitting"
                />
              </div>
              <div>
                <label class="form-label" for="jira-password">{{ t('jira.authPassword') }}</label>
                <input
                  id="jira-password"
                  class="form-control"
                  type="password"
                  v-model="authPassword"
                  :disabled="isSubmitting"
                />
              </div>
            </div>
          </div>

          <div class="jira-summary mb-3" v-if="report">
            <div class="jira-summary-title">{{ t('jira.summaryHeading') }}</div>
            <ul class="list-unstyled">
              <li>{{ t('jira.summaryRun') }}: {{ report.run_id }}</li>
              <li>{{ t('jira.summaryBugs') }}: {{ report.bug_count || 0 }}</li>
              <li>{{ t('jira.summaryAsos') }}: {{ report.aso_count || 0 }}</li>
              <li>{{ t('jira.summaryTotal') }}: {{ report.total || 0 }}</li>
            </ul>
          </div>

          <div v-if="errorMessage" class="alert alert-danger" role="alert">
            {{ errorMessage }}
          </div>

          <div class="jira-modal-actions">
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="!canSubmit"
            >
              {{ t('jira.submit') }}
            </button>
            <button type="button" class="btn btn-outline-secondary" @click="emitCancel" :disabled="isSubmitting">
              {{ t('jira.cancel') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { computed, watch, ref } from "vue";
import { sanitizeNoteText } from "../../lib/notes";
import { t } from "../../lib/i18n";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  report: {
    type: Object,
    default: null,
  },
  defaultTicket: {
    type: String,
    default: "",
  },
  defaultNote: {
    type: String,
    default: "",
  },
  defaultUsername: {
    type: String,
    default: "",
  },
  defaultPassword: {
    type: String,
    default: "",
  },
  defaultMode: {
    type: String,
    default: "auto",
  },
  authConfigured: {
    type: Boolean,
    default: false,
  },
  authMode: {
    type: String,
    default: "basic",
  },
  errorMessage: {
    type: String,
    default: "",
  },
  isSubmitting: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["submit", "cancel"]);
const ticketInput = ref("");
const noteDraft = ref("");
const authUsername = ref("");
const authPassword = ref("");
const authToken = ref("");
const modeInput = ref("auto");
const ticketRegex = /^[A-Z][A-Z0-9]+-[0-9]+$/;

function normalizeMode(value) {
  const mode = String(value || "").trim().toLowerCase();
  if (mode === "comment" || mode === "subtask") {
    return mode;
  }
  return "auto";
}

watch(
  () => props.visible,
  (visible) => {
    if (!visible) return;
    ticketInput.value = props.defaultTicket || "";
    noteDraft.value = props.defaultNote || "";
    authUsername.value = props.defaultUsername || "";
    authPassword.value = props.defaultPassword || "";
    authToken.value = "";
    modeInput.value = normalizeMode(props.defaultMode);
  }
);

const ticketValue = computed(() => (ticketInput.value || "").trim());
const ticketValid = computed(() => ticketRegex.test(ticketValue.value.toUpperCase()));
const noteValue = computed(() => sanitizeNoteText(noteDraft.value));
const modeValue = computed(() => normalizeMode(modeInput.value));
const authRequired = computed(() => !props.authConfigured);
const authReady = computed(() => {
  if (!authRequired.value) {
    return true;
  }
  if (props.authMode === "token") {
    return Boolean(authToken.value.trim());
  }
  return Boolean(authUsername.value.trim()) && Boolean(authPassword.value.trim());
});
const canSubmit = computed(() => ticketValid.value && authReady.value && !props.isSubmitting);

const emitCancel = () => {
  emit("cancel");
};

const handleSubmit = () => {
  if (!canSubmit.value) return;
  const payload = {
    ticket: ticketValue.value.toUpperCase(),
    note: noteValue.value,
    mode: modeValue.value,
  };
  if (authRequired.value) {
    payload.auth = {
      username: authUsername.value.trim(),
      password: authPassword.value.trim(),
      api_token: authToken.value.trim(),
      mode: props.authMode,
    };
  }
  emit("submit", payload);
};
</script>

<style scoped>
.jira-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.jira-modal-card {
  background: var(--card-bg);
  border-radius: 1rem;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.3);
  width: min(540px, 100%);
  padding: 1.25rem 1.5rem;
}

.jira-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.jira-modal-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.jira-modal-body {
  display: flex;
  flex-direction: column;
}

.jira-auth-title {
  font-weight: 600;
}

.jira-auth-hint {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.jira-summary {
  padding: 0.75rem 1rem;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  background: var(--card-bg);
}

.jira-summary-title {
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.jira-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
}
</style>

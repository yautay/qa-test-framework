<template>
  <div class="card shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead class="table-light">
          <tr>
            <th>{{ t('listing.scenario') }}</th>
            <th class="small-col">{{ t('listing.browser') }}</th>
            <th class="small-col">{{ t('listing.viewport') }}</th>
            <th class="small-col">{{ t('listing.signals') }}</th>
            <th class="small-col">{{ t('listing.status') }}</th>
            <th class="small-col">{{ t('listing.pixel') }}</th>
            <th class="small-col">{{ t('listing.lpips') }}</th>
            <th class="small-col">{{ t('listing.dists') }}</th>
            <th>{{ t('listing.message') }}</th>
            <th>{{ t('listing.artifacts') }}</th>
            <th class="small-col text-end">{{ t('listing.metadata') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, index) in rows" :key="rowKey(r, index)" 
              :class="{ 'table-active': index === selectedIndex }"
              @click="$emit('select', index)"
              @dblclick="$emit('show', r, 'test', index)">
            <td class="mono">
              <span>{{ r.scenario_id }}</span>
            </td>

            <td class="small-col">
              <span v-if="r.browser"
                class="badge badge-browser"
                :style="badgeStyle('browser', r.browser)"
              >
                {{ r.browser }}
              </span>
            </td>

            <td class="small-col">
              <span v-if="r.viewport"
                class="badge badge-viewport"
                :style="badgeStyle('viewport', r.viewport)"
              >
                {{ r.viewport }}
              </span>
            </td>

            <td class="small-col">
              <div class="d-flex gap-1 align-items-center">
                <span
                  v-if="rowHasPmsPending(r)"
                  class="badge bg-secondary pms-pending-icon"
                  :title="getPmsPendingTitle(r)"
                >
                  ⏳
                </span>
                <span
                  v-if="rowHasPmsError(r)"
                  class="badge bg-warning text-dark pms-error-icon"
                  :title="getPmsErrorTitle(r)"
                >
                  ⚠
                </span>
                <span
                  v-if="rowHasPmsSuccess(r)"
                  class="badge bg-success pms-success-icon"
                  :title="getPmsSuccessTitle(r)"
                >
                  ✅
                </span>
                <span
                  v-if="rowHasSyncIssue(r)"
                  class="badge bg-warning text-dark sync-error-icon"
                  :title="getSyncIssueMessage(r)"
                >
                  ⚠
                </span>
              </div>
            </td>

            <td class="small-col">
                <span class="badge"
                :class="statusClass(r.status)">{{ statusLabel(r.status) }}</span>
            </td>

            <td class="small-col mono">{{ fmt(r.pixel_changed_ratio) }}</td>
            <td class="small-col mono">{{ fmt(r.lpips) }}</td>
            <td class="small-col mono">{{ fmt(r.dists) }}</td>
            <td style="max-width: 420px;">
              <div class="d-flex flex-wrap gap-1 mb-1">
                <span v-if="rowHasTag(r, 'bug')" 
                      class="badge bg-danger"
                      :class="{ 'tag-pending': isPendingTag(r, 'bug') }">
                  {{ t('tags.bug') }}
                </span>
                <span v-if="rowHasTag(r, 'aso')" 
                      class="badge bg-warning text-dark"
                      :class="{ 'tag-pending': isPendingTag(r, 'aso') }">
                  {{ t('tags.aso') }}
                </span>
                <span v-if="rowHasTag(r, 'baseline')" class="badge bg-success">{{ t('tags.baseline') }}</span>
              </div>
              <div>{{ messageLabel(r.message) }}</div>
            </td>

            <td style="min-width: 430px;">
              <div class="d-flex flex-wrap gap-2 artifact-icons">
                <span v-if="r.baseline_path" class="artifact-badge artifact-ref">{{ t('artifacts.ref') }}</span>
                <span v-if="r.actual_path" class="artifact-badge artifact-test">{{ t('artifacts.test') }}</span>
                <span v-if="r.diff_path" class="artifact-badge artifact-diff">{{ t('artifacts.diff') }}</span>
                <span v-if="r.heatmap_path" class="artifact-badge artifact-perc">{{ t('artifacts.lpips') }}</span>
              </div>
            </td>

            <td class="small-col text-end">
              <button
                type="button"
                class="btn btn-sm btn-outline-secondary metadata-icon"
                :title="t('metadata.open')"
                @click.stop="$emit('open-metadata', r, index)"
              >
                i
              </button>
            </td>
          </tr>

          <tr v-if="rows.length===0">
            <td colspan="11" class="text-center text-muted py-4">{{ t('listing.noResults') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { t } from "../lib/i18n";
import { badgeStyle as computeBadgeStyle } from "../lib/badgeStyle";
import { statusBadgeClass } from "../lib/statusClass";

export default {
  name: "ResultsTable",
  props: {
    rows: {
      type: Array,
      default: () => [],
    },
    fmt: {
      type: Function,
      required: true,
    },
    tagLog: {
      type: Object,
      default: () => ({}),
    },
    tagKeyForRow: {
      type: Function,
      default: () => "",
    },
    selectedIndex: {
      type: Number,
      default: -1,
    },
    syncErrors: {
      type: Object,
      default: () => ({}),
    },
    pendingTags: {
      type: Object,
      default: () => ({}),
    },
  },
  emits: ["show", "select", "open-metadata"],
  methods: {
    t(key) {
      return t(key);
    },
    statusClass(status) {
      return statusBadgeClass(status);
    },
    statusLabel(status) {
      if (!status) return "";
      const normalized = String(status).toLowerCase();
      const key = `status.${normalized}`;
      const translation = this.t(key);
      if (translation && translation !== key) {
        return translation;
      }
      return status;
    },
    messageLabel(message) {
      const normalized = String(message || "").trim().toLowerCase();
      if (!normalized) return "";
      const mapping = {
        "pixel threshold exceeded": "message.pixelThresholdExceeded",
        "pixel threshold passed": "message.pixelThresholdPassed",
        "pixel within uncertainty zone": "message.pixelWithinUncertaintyZone",
        "baseline missing": "message.baselineMissing",
      };
      const key = mapping[normalized];
      if (!key) return String(message || "");
      const translation = this.t(key);
      if (translation && translation !== key) {
        return translation;
      }
      return String(message || "");
    },
    rowHasTag(row, tag) {
      const key = this.tagKeyForRow(row);
      const tags = this.tagLog?.[key];
      if (!tags) return false;
      if (tag === "bug") return !!tags.bug?.locked;
      if (tag === "aso") return !!tags.aso?.locked;
      if (tag === "baseline") return !!tags.baseline;
      return false;
    },
    rowKey(row, index) {
      const key = this.tagKeyForRow(row);
      if (key) return key;
      return `${row?.scenario_id || "row"}::${row?.viewport || ""}::${row?.browser || ""}::${index}`;
    },
    badgeStyle(type, value) {
      return computeBadgeStyle(type, value);
    },
    getPerceptualStatus(row) {
      const perceptual = row?.perceptual;
      if (!perceptual || typeof perceptual !== "object") return "";
      return String(perceptual.status || "").trim().toLowerCase();
    },
    rowHasPmsPending(row) {
      const status = this.getPerceptualStatus(row);
      return status === "queued" || status === "running";
    },
    rowHasPmsError(row) {
      const status = this.getPerceptualStatus(row);
      return status === "error" || status === "timeout";
    },
    rowHasPmsSuccess(row) {
      return this.getPerceptualStatus(row) === "done";
    },
    getPmsPendingTitle(_row) {
      return t("pms.pendingTest");
    },
    getPmsErrorTitle(row) {
      const message = String(row?.perceptual?.error_message || "").trim();
      if (message) return `${t("pms.errorTest")}: ${message}`;
      return t("pms.errorTestUnknown");
    },
    getPmsSuccessTitle(_row) {
      return t("pms.successTest");
    },
    getSyncIssue(row) {
      const key = this.tagKeyForRow(row);
      if (!key) return { hasIssue: false, title: "" };
      const tags = this.tagLog?.[key] || {};
      const pending = this.pendingTags?.[key] || {};
      const syncError = this.syncErrors?.[key] || null;
      const bugUnsynced = !!tags.bug?.locked && !tags.bug?.synced;
      const asoUnsynced = !!tags.aso?.locked && !tags.aso?.synced;
      const bugPending = !!pending.bug;
      const asoPending = !!pending.aso;

      if (syncError) {
        const message = syncError.message || t("sync.unknown");
        return {
          hasIssue: true,
          title: `${t("sync.errorPrefix")}: ${message}`,
        };
      }

      if (bugPending || asoPending) {
        return {
          hasIssue: true,
          title: t("sync.pendingTooltip"),
        };
      }

      if (bugUnsynced || asoUnsynced) {
        return {
          hasIssue: true,
          title: t("sync.unsyncedTooltip"),
        };
      }

      return { hasIssue: false, title: "" };
    },
    rowHasSyncIssue(row) {
      return this.getSyncIssue(row).hasIssue;
    },
    getSyncIssueMessage(row) {
      return this.getSyncIssue(row).title;
    },
    isPendingTag(row, tagType) {
      const key = this.tagKeyForRow(row);
      return !!this.pendingTags?.[key]?.[tagType];
    },
    _perceptualPayload(row) {
      if (row?.perceptual && typeof row.perceptual === "object") {
        return row.perceptual;
      }
      const nested = row?.test_metadata?.perceptual;
      if (nested && typeof nested === "object") {
        return nested;
      }
      return null;
    },
    _expectsPerceptual(row) {
      const mode = String(row?.compare_mode || "").toLowerCase();
      return mode === "perceptual" || mode === "hybrid";
    },
    _perceptualIssue(row) {
      if (!this._expectsPerceptual(row)) {
        return { hasIssue: false, icon: "", className: "", title: "" };
      }
      const payload = this._perceptualPayload(row);
      const status = String(payload?.status || "").toLowerCase();
      const errorMessage = String(payload?.error_message || "").trim();
      const hasScores = row?.lpips != null || row?.dists != null;

      const pendingStatuses = new Set(["queued", "pending", "submitted", "running"]);
      const warningStatuses = new Set(["error", "timeout", "skipped", "failed"]);

      if (pendingStatuses.has(status)) {
        const detail = this._perceptualStatusLabel(status);
        return {
          hasIssue: true,
          icon: "⏳",
          className: "bg-info text-dark",
          title: `${this.t("pms.pendingTooltip")}: ${detail}`,
        };
      }

      if (warningStatuses.has(status)) {
        const detail = this._perceptualStatusLabel(status);
        const suffix = errorMessage ? ` - ${errorMessage}` : "";
        return {
          hasIssue: true,
          icon: "⚠",
          className: "bg-warning text-dark",
          title: `${this.t("pms.issueTooltip")}: ${detail}${suffix}`,
        };
      }

      if (!payload && !hasScores) {
        return {
          hasIssue: true,
          icon: "⚠",
          className: "bg-warning text-dark",
          title: this.t("pms.missingTooltip"),
        };
      }

      return { hasIssue: false, icon: "", className: "", title: "" };
    },
    _perceptualStatusLabel(status) {
      const normalized = String(status || "").toLowerCase();
      if (!normalized) {
        return this.t("pms.status.unknown");
      }
      const key = `pms.status.${normalized}`;
      const translated = this.t(key);
      if (translated && translated !== key) {
        return translated;
      }
      return normalized;
    },
    rowHasPerceptualIssue(row) {
      return this._perceptualIssue(row).hasIssue;
    },
    getPerceptualIssueMessage(row) {
      return this._perceptualIssue(row).title;
    },
    getPerceptualIssueIcon(row) {
      return this._perceptualIssue(row).icon;
    },
    perceptualIssueClass(row) {
      return this._perceptualIssue(row).className;
    },
  },
};
</script>

<style scoped>
.card {
  background-color: var(--card-bg);
  border-color: var(--border);
}

.table {
  --bs-table-bg: var(--card-bg);
  color: var(--body-color);
  border-color: var(--border);
}

.table thead th {
  background-color: var(--body-bg);
  color: var(--body-color);
  border-color: var(--border);
}

.table tbody td {
  background-color: var(--card-bg);
  color: var(--body-color);
  border-color: var(--border);
}

.table tbody tr:hover td {
  background-color: var(--body-bg);
}

.table-light {
  --bs-table-bg: var(--body-bg);
  color: var(--body-color);
}

.small-col {
  white-space: nowrap;
}

.artifact-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: 0.25rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.badge-viewport,
.badge-browser {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.artifact-ref {
  background-color: var(--primary);
  color: white;
  opacity: 0.85;
}

.artifact-test {
  background-color: var(--success);
  color: white;
  opacity: 0.85;
}

.artifact-diff {
  background-color: var(--danger);
  color: white;
  opacity: 0.85;
}

.artifact-perc {
  background-color: var(--warning);
  color: #212529;
  opacity: 0.85;
}

.table-active {
  background-color: var(--body-bg) !important;
}

.pms-pending-icon,
.pms-error-icon,
.pms-success-icon,
.sync-error-icon {
  min-width: 1.5rem;
  text-align: center;
}

.metadata-icon {
  width: 1.8rem;
  height: 1.8rem;
  border-radius: 999px;
  padding: 0;
  font-weight: 700;
  line-height: 1;
}

.tag-pending {
  animation: pulse-tag 1.5s infinite;
  box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.7);
}

@keyframes pulse-tag {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}
</style>

import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import ReportCard from "./ReportCard.vue";

describe("ReportCard", () => {
  it("renders stats and link to report", () => {
    const wrapper = mount(ReportCard, {
      props: {
        report: {
          run_id: "20260218_120000_000001",
          total: 12,
          passed: 7,
          failed: 4,
          new: 1,
          updated_at: "2026-02-18 12:00:00",
          summary: "failed=4 passed=7 new=1",
          tester: "jan.k",
          run_note: "manual smoke",
          run_metadata: {
            target_git_info: {
              frontend: {
                branch: "feature/front",
                commit: "abc1234",
                status: "ok",
              },
              backend: {
                status: "not_configured",
              },
            },
          },
        },
      },
    });

    expect(wrapper.text()).toContain("20260218_120000_000001");
    expect(wrapper.text()).toContain("12 tests");
    expect(wrapper.find(".text-bg-success").text()).toBe("7");
    expect(wrapper.find(".text-bg-danger").text()).toBe("4");
    expect(wrapper.text()).toContain("Tester: jan.k");
    expect(wrapper.text()).toContain("Run note: manual smoke");
    expect(wrapper.text()).toContain("Frontend branch: feature/front @ abc1234");
    expect(wrapper.text()).toContain("Backend branch: not configured");
    expect(wrapper.find("a.btn").attributes("href")).toBe("/reports/20260218_120000_000001");
  });

  it("shows sync warning badge with diagnostic counters", () => {
    const wrapper = mount(ReportCard, {
      props: {
        report: {
          run_id: "20260218_120000_000001",
          total: 10,
          passed: 5,
          failed: 5,
          has_sync_issues: true,
          sync_failed_count: 2,
          sync_pending_count: 3,
          sync_sending_count: 1,
          sync_unsynced_count: 4,
        },
      },
    });

    const warning = wrapper.find(".sync-warning-icon");
    expect(warning.exists()).toBe(true);
    expect(warning.attributes("title")).toContain("failed: 2");
    expect(warning.attributes("title")).toContain("pending: 3");
    expect(warning.attributes("title")).toContain("sending: 1");
    expect(warning.attributes("title")).toContain("unsynced: 4");
  });

  it("does not show warning badge when report has no sync issues", () => {
    const wrapper = mount(ReportCard, {
      props: {
        report: {
          run_id: "run-ok",
          total: 4,
          passed: 4,
          failed: 0,
          has_sync_issues: false,
          sync_failed_count: 0,
          sync_pending_count: 0,
          sync_sending_count: 0,
          sync_unsynced_count: 0,
        },
      },
    });

    expect(wrapper.find(".sync-warning-icon").exists()).toBe(false);
  });

  it("shows warning badge when hasSyncErrors fallback prop is true", () => {
    const wrapper = mount(ReportCard, {
      props: {
        hasSyncErrors: true,
        report: {
          run_id: "run-fallback",
          total: 4,
          passed: 4,
          failed: 0,
          has_sync_issues: false,
          sync_failed_count: 0,
          sync_pending_count: 0,
          sync_sending_count: 0,
          sync_unsynced_count: 0,
        },
      },
    });

    const warning = wrapper.find(".sync-warning-icon");
    expect(warning.exists()).toBe(true);
    expect(warning.attributes("title")).toContain("failed: 0");
    expect(warning.attributes("title")).toContain("pending: 0");
    expect(warning.attributes("title")).toContain("sending: 0");
    expect(warning.attributes("title")).toContain("unsynced: 0");
  });

  it("shows PMS pending, error and success signals with counters", () => {
    const wrapper = mount(ReportCard, {
      props: {
        report: {
          run_id: "run-pms",
          total: 10,
          pms_pending_count: 2,
          pms_error_count: 1,
          pms_success_count: 7,
        },
      },
    });

    expect(wrapper.find(".pms-signal.bg-secondary").attributes("title")).toContain("2");
    expect(wrapper.find(".pms-signal.bg-warning").attributes("title")).toContain("1");
    expect(wrapper.find(".pms-signal.bg-success").attributes("title")).toContain("7");
  });
});

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
        },
      },
    });

    expect(wrapper.text()).toContain("20260218_120000_000001");
    expect(wrapper.text()).toContain("12 tests");
    expect(wrapper.find(".text-bg-success").text()).toBe("7");
    expect(wrapper.find(".text-bg-danger").text()).toBe("4");
    expect(wrapper.text()).toContain("Tester: jan.k");
    expect(wrapper.text()).toContain("Run note: manual smoke");
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

    const warning = wrapper.find(".badge.bg-warning.text-dark");
    expect(warning.exists()).toBe(true);
    expect(warning.attributes("title")).toContain("failed: 2");
    expect(warning.attributes("title")).toContain("pending: 3");
    expect(warning.attributes("title")).toContain("sending: 1");
    expect(warning.attributes("title")).toContain("unsynced: 4");
  });
});

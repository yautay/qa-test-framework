import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { mount } from "@vue/test-utils";
import { ref } from "vue";

import SyncToasts from "./SyncToasts.vue";

const mockAlerts = ref([]);
const mockDismissToast = vi.fn();

vi.mock('../composables/useSyncAlerts', () => ({
  useSyncAlerts: () => ({
    alerts: mockAlerts,
    dismissToast: mockDismissToast,
  }),
}));

describe("SyncToasts", () => {
  beforeEach(() => {
    mockAlerts.value = [];
    mockDismissToast.mockClear();
  });

  it("renders nothing when no alerts", async () => {
    const wrapper = mount(SyncToasts);
    expect(wrapper.find(".toast-container").exists()).toBe(true);
    expect(wrapper.findAll(".toast")).toHaveLength(0);
  });

  it("renders alerts when present", async () => {
    mockAlerts.value = [
      { id: 1, message: "Test message 1", type: "warning" },
      { id: 2, message: "Test message 2", type: "error" },
    ];

    const wrapper = mount(SyncToasts);
    const toasts = wrapper.findAll(".toast");
    expect(toasts).toHaveLength(2);
    expect(toasts[0].text()).toContain("Test message 1");
    expect(toasts[1].text()).toContain("Test message 2");
  });

  it("applies correct CSS class for warning type", async () => {
    mockAlerts.value = [{ id: 1, message: "Warning", type: "warning" }];

    const wrapper = mount(SyncToasts);
    const toast = wrapper.find(".toast");
    expect(toast.classes()).toContain("bg-warning");
  });

  it("applies correct CSS class for error type", async () => {
    mockAlerts.value = [{ id: 1, message: "Error", type: "error" }];

    const wrapper = mount(SyncToasts);
    const toast = wrapper.find(".toast");
    expect(toast.classes()).toContain("bg-danger");
  });

  it("applies correct CSS class for success type", async () => {
    mockAlerts.value = [{ id: 1, message: "Success", type: "success" }];

    const wrapper = mount(SyncToasts);
    const toast = wrapper.find(".toast");
    expect(toast.classes()).toContain("bg-success");
  });

  it("applies correct CSS class for info type", async () => {
    mockAlerts.value = [{ id: 1, message: "Info", type: "info" }];

    const wrapper = mount(SyncToasts);
    const toast = wrapper.find(".toast");
    expect(toast.classes()).toContain("bg-info");
  });

  it("applies fallback warning class for unknown type", async () => {
    mockAlerts.value = [{ id: 1, message: "Unknown", type: "unknown" }];

    const wrapper = mount(SyncToasts);
    const toast = wrapper.find(".toast");
    expect(toast.classes()).toContain("bg-warning");
  });

  it("calls dismissToast when close button is clicked", async () => {
    mockAlerts.value = [{ id: 123, message: "Test", type: "warning" }];

    const wrapper = mount(SyncToasts);
    const closeButton = wrapper.find(".btn-close");
    await closeButton.trigger("click");

    expect(mockDismissToast).toHaveBeenCalledWith(123);
  });

  it("renders multiple alerts with different types", async () => {
    mockAlerts.value = [
      { id: 1, message: "Warning", type: "warning" },
      { id: 2, message: "Error", type: "error" },
      { id: 3, message: "Success", type: "success" },
      { id: 4, message: "Info", type: "info" },
    ];

    const wrapper = mount(SyncToasts);
    const toasts = wrapper.findAll(".toast");

    expect(toasts[0].classes()).toContain("bg-warning");
    expect(toasts[1].classes()).toContain("bg-danger");
    expect(toasts[2].classes()).toContain("bg-success");
    expect(toasts[3].classes()).toContain("bg-info");
  });
});

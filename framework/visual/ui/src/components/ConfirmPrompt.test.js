import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";

vi.mock("../lib/i18n", () => ({
  t: (key) => key,
}));

import ConfirmPrompt from "./ConfirmPrompt.vue";

describe("ConfirmPrompt", () => {
  it("renders send-report prompt in global overlay", () => {
    const wrapper = mount(ConfirmPrompt, {
      props: {
        active: true,
        type: "send-report",
      },
    });

    expect(wrapper.find(".global-prompt-overlay").exists()).toBe(true);
    expect(wrapper.text()).toContain("report.confirmSend");
  });

  it("renders modal tag prompt with note textarea and counter", () => {
    const host = document.createElement("div");
    host.id = "vrtModal";
    const content = document.createElement("div");
    content.className = "modal-content";
    host.appendChild(content);
    document.body.appendChild(host);

    const wrapper = mount(ConfirmPrompt, {
      attachTo: document.body,
      props: {
        active: true,
        type: "bug",
        note: "abc",
        noteMaxLength: 10,
      },
    });

    const textarea = document.querySelector("#vrtModal .modal-content .prompt-textarea");
    const counter = document.querySelector("#vrtModal .modal-content .prompt-counter");

    expect(document.querySelector("#vrtModal .modal-content .global-prompt-overlay")).toBeTruthy();
    expect(textarea).toBeTruthy();
    expect(counter?.textContent).toContain("3/10");

    wrapper.unmount();
    host.remove();
  });

  it("emits note-input and confirm/cancel actions", async () => {
    const host = document.createElement("div");
    host.id = "vrtModal";
    const content = document.createElement("div");
    content.className = "modal-content";
    host.appendChild(content);
    document.body.appendChild(host);

    const wrapper = mount(ConfirmPrompt, {
      attachTo: document.body,
      props: {
        active: true,
        type: "aso",
        note: "",
      },
    });

    const textarea = document.querySelector("#vrtModal .modal-content .prompt-textarea");
    textarea.value = "note";
    textarea.dispatchEvent(new Event("input"));

    const confirmBtn = document.querySelector("#vrtModal .modal-content .btn-primary");
    const cancelBtn = document.querySelector("#vrtModal .modal-content .btn-outline-secondary");
    confirmBtn.dispatchEvent(new MouseEvent("click"));
    cancelBtn.dispatchEvent(new MouseEvent("click"));

    await nextTick();

    expect(wrapper.emitted("note-input")).toBeTruthy();
    expect(wrapper.emitted("note-input")[0][0]).toBe("note");
    expect(wrapper.emitted("confirm")).toBeTruthy();
    expect(wrapper.emitted("cancel")).toBeTruthy();

    wrapper.unmount();
    host.remove();
  });

  it("renders remove prompt and computes remove type label", () => {
    const host = document.createElement("div");
    host.id = "vrtModal";
    const content = document.createElement("div");
    content.className = "modal-content";
    host.appendChild(content);
    document.body.appendChild(host);

    const wrapper = mount(ConfirmPrompt, {
      attachTo: document.body,
      props: {
        active: true,
        type: "remove-baseline",
      },
    });

    const promptText = document.querySelector("#vrtModal .modal-content")?.textContent || "";
    expect(promptText).toContain("prompt.removeTag");
    expect(promptText).toContain("tags.baseline");

    wrapper.unmount();
    host.remove();
  });

  it("focuses note input when bug prompt becomes active", async () => {
    const host = document.createElement("div");
    host.id = "vrtModal";
    const content = document.createElement("div");
    content.className = "modal-content";
    host.appendChild(content);
    document.body.appendChild(host);

    const focusSpy = vi.spyOn(HTMLTextAreaElement.prototype, "focus").mockImplementation(() => {});
    const wrapper = mount(ConfirmPrompt, {
      attachTo: document.body,
      props: {
        active: false,
        type: null,
      },
    });

    await wrapper.setProps({ active: true, type: "bug" });
    await nextTick();
    await nextTick();

    expect(focusSpy).toHaveBeenCalled();

    focusSpy.mockRestore();
    wrapper.unmount();
    host.remove();
  });
});

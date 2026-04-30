import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";

import JiraSendModal from "./JiraSendModal.vue";

describe("JiraSendModal", () => {
  it("prefills ticket, note, credentials and mode on open", async () => {
    const wrapper = mount(JiraSendModal, {
      props: {
        visible: false,
        report: { run_id: "run-1" },
        defaultTicket: "NN-123",
        defaultNote: "from settings_cli",
        defaultUsername: "qa.user",
        defaultPassword: "top-secret",
        defaultMode: "auto",
        authConfigured: false,
        authMode: "basic",
      },
      global: {
        stubs: {
          teleport: true,
        },
      },
    });

    await wrapper.setProps({ visible: true });
    await nextTick();

    expect(wrapper.get("#jira-ticket").element.value).toBe("NN-123");
    expect(wrapper.get("#jira-note").element.value).toBe("from settings_cli");
    expect(wrapper.get("#jira-username").element.value).toBe("qa.user");
    expect(wrapper.get("#jira-password").element.value).toBe("top-secret");
    expect(wrapper.get("#jira-mode").element.value).toBe("auto");

    wrapper.unmount();
  });

  it("emits editable payload with selected mode", async () => {
    const wrapper = mount(JiraSendModal, {
      props: {
        visible: false,
        report: { run_id: "run-1" },
        defaultTicket: "NN-123",
        defaultNote: "default note",
        defaultUsername: "default.user",
        defaultPassword: "default-pass",
        defaultMode: "auto",
        authConfigured: false,
        authMode: "basic",
      },
      global: {
        stubs: {
          teleport: true,
        },
      },
    });

    await wrapper.setProps({ visible: true });
    await nextTick();

    await wrapper.get("#jira-ticket").setValue("abc-77");
    await wrapper.get("#jira-note").setValue("  updated note  ");
    await wrapper.get("#jira-username").setValue("  manual.user  ");
    await wrapper.get("#jira-password").setValue("  manual-pass  ");
    await wrapper.get("#jira-mode").setValue("subtask");
    await wrapper.get("form").trigger("submit.prevent");

    const emitted = wrapper.emitted("submit") || [];
    expect(emitted).toHaveLength(1);
    expect(emitted[0][0]).toEqual({
      ticket: "ABC-77",
      note: "updated note",
      mode: "subtask",
      auth: {
        username: "manual.user",
        password: "manual-pass",
        api_token: "",
        mode: "basic",
      },
    });

    wrapper.unmount();
  });
});

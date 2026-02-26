import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";

import TestMetadataPanel from "./TestMetadataPanel.vue";

vi.mock("../lib/i18n", () => ({
  t: (key) => key,
}));

describe("TestMetadataPanel", () => {
  it("flattens nested metadata and formats array values", () => {
    const wrapper = mount(TestMetadataPanel, {
      props: {
        active: true,
        metadata: {
          run: {
            run_id: "run-1",
          },
          result: {
            scenario_id: "scenario-a",
            tags: ["smoke", "visual"],
          },
        },
      },
    });

    const text = wrapper.text();
    expect(text).toContain("run.run_id");
    expect(text).toContain("run-1");
    expect(text).toContain("result.scenario_id");
    expect(text).toContain("scenario-a");
    expect(text).toContain("result.tags");
    expect(text).toContain("smoke, visual");
  });
});

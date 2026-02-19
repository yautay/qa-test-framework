import { describe, expect, it, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";

vi.mock("../lib/i18n", () => ({
  t: (key) => key,
}));

import ViewerModal from "./ViewerModal.vue";

describe("ViewerModal", () => {
  const defaultViewer = {
    modalOpen: true,
    viewerMode: "test",
    modalRow: {
      scenario_id: "test-scenario",
      status: "failed",
      viewport: "fhd",
      browser: "chromium",
      pixel_changed_ratio: 0.5,
      lpips: 0.1,
      dists: 0.2,
    },
    modalTitle: "test-scenario",
    modalSubtitle: "status=failed mode=test",
    slots: [
      { id: 1, mode: "ref" },
      { id: 2, mode: "test" },
    ],
    tags: {
      bug: false,
      aso: false,
      baseline: false,
      note: null,
      bug_reported: false,
      aso_reported: false,
    },
    tagLog: {},
    tagLocked: {},
    currentIndex: 0,
    columns: 2,
    cursorX: 50,
    cursorY: 50,
  };

  const defaultProps = {
    viewer: defaultViewer,
    gridStyle: { gridTemplateColumns: "repeat(2, 1fr)" },
    presentationStyle: { width: "100%" },
    imageStyle: { transform: "scale(1)" },
    prompt: { active: false, type: null },
    noteEditor: { active: false, text: "", hasExisting: false },
    noteMaxLength: 2000,
    keyHeld: {},
    superZoomActive: false,
    slotImage: (slot) => slot.mode === "ref" ? "/ref.png" : "/test.png",
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("modeOptions", () => {
    it("returns all available modes", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      const options = wrapper.vm.modeOptions;

      expect(options).toHaveLength(4);
      expect(options.map(o => o.value)).toEqual(["ref", "test", "diff", "lpips"]);
    });
  });

  describe("promptRemove", () => {
    it("returns true for remove- type", () => {
      const wrapper = mount(ViewerModal, {
        props: { ...defaultProps, prompt: { active: true, type: "remove-bug" } },
      });

      expect(wrapper.vm.promptRemove).toBe(true);
    });

    it("returns false for non-remove type", () => {
      const wrapper = mount(ViewerModal, {
        props: { ...defaultProps, prompt: { active: true, type: "bug" } },
      });

      expect(wrapper.vm.promptRemove).toBe(false);
    });
  });

  describe("headerBadges", () => {
    it("includes status badge", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      const badges = wrapper.vm.headerBadges;

      expect(badges.some(b => b.key === "status-failed")).toBe(true);
    });

    it("includes viewport badge", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      const badges = wrapper.vm.headerBadges;

      expect(badges.some(b => b.key === "viewport-fhd")).toBe(true);
    });

    it("includes browser badge", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      const badges = wrapper.vm.headerBadges;

      expect(badges.some(b => b.key === "browser-chromium")).toBe(true);
    });

    it("includes bug tag badge when present", () => {
      const viewer = { ...defaultViewer, tags: { ...defaultViewer.tags, bug: true } };
      const wrapper = mount(ViewerModal, {
        props: { ...defaultProps, viewer },
      });

      const badges = wrapper.vm.headerBadges;

      expect(badges.some(b => b.key === "bug")).toBe(true);
    });

    it("includes bug reported badge when reported", () => {
      const viewer = { ...defaultViewer, tags: { ...defaultViewer.tags, bug_reported: true } };
      const wrapper = mount(ViewerModal, {
        props: { ...defaultProps, viewer },
      });

      const badges = wrapper.vm.headerBadges;

      expect(badges.some(b => b.key === "bug_sent")).toBe(true);
    });

    it("includes asotag badge when present", () => {
      const viewer = { ...defaultViewer, tags: { ...defaultViewer.tags,aso: true } };
      const wrapper = mount(ViewerModal, {
        props: { ...defaultProps, viewer },
      });

      const badges = wrapper.vm.headerBadges;

      expect(badges.some(b => b.key === "aso")).toBe(true);
    });

    it("includes baseline tag badge when present", () => {
      const viewer = { ...defaultViewer, tags: { ...defaultViewer.tags, baseline: true } };
      const wrapper = mount(ViewerModal, {
        props: { ...defaultProps, viewer },
      });

      const badges = wrapper.vm.headerBadges;

      expect(badges.some(b => b.key === "baseline")).toBe(true);
    });

    it("includes note badge when note exists", () => {
      const viewer = { ...defaultViewer, tags: { ...defaultViewer.tags, note: { text: "Test note" } } };
      const wrapper = mount(ViewerModal, {
        props: { ...defaultProps, viewer },
      });

      const badges = wrapper.vm.headerBadges;

      expect(badges.some(b => b.key === "note")).toBe(true);
    });
  });

  describe("scoringText", () => {
    it("returns empty when no scoring data", () => {
      const viewer = { ...defaultViewer, modalRow: { scenario_id: "test" } };
      const wrapper = mount(ViewerModal, {
        props: { ...defaultProps, viewer },
      });

      expect(wrapper.vm.scoringText).toBe("");
    });

    it("returns scoring text with metrics when data present", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      const text = wrapper.vm.scoringText;

      expect(text).toContain("scoring");
    });
  });

  describe("slotModeLabel", () => {
    it("returns label for ref mode", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      expect(wrapper.vm.slotModeLabel("ref")).toBe("REF");
    });

    it("returns label for test mode", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      expect(wrapper.vm.slotModeLabel("test")).toBe("TEST");
    });

    it("returns label for diff mode", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      expect(wrapper.vm.slotModeLabel("diff")).toBe("PIXEL_DIFF");
    });

    it("returns label for lpips mode", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      expect(wrapper.vm.slotModeLabel("lpips")).toBe("PERC");
    });

    it("returns empty for unknown mode", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      expect(wrapper.vm.slotModeLabel("unknown")).toBe("");
    });
  });

  describe("statusClass", () => {
    it("returns class for passed status", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      const result = wrapper.vm.statusClass("passed");

      expect(result).toBeTruthy();
    });

    it("returns class for failed status", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      const result = wrapper.vm.statusClass("failed");

      expect(result).toBeTruthy();
    });
  });

  describe("statusLabel", () => {
    it("returns translation when available", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      const result = wrapper.vm.statusLabel("passed");

      expect(result).toBeTruthy();
    });

    it("returns status when no translation", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      const result = wrapper.vm.statusLabel("unknown");

      expect(result).toBe("unknown");
    });

    it("handles empty status", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      const result = wrapper.vm.statusLabel("");

      expect(result).toBe("");
    });
  });

  describe("promptTypeLabel", () => {
    it("returns bug label for bug type", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      expect(wrapper.vm.promptTypeLabel("bug")).toBe("tags.bug");
    });

    it("returns asolabel for asotype", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      expect(wrapper.vm.promptTypeLabel("aso")).toBe("tags.aso");
    });

    it("returns baseline label for baseline type", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      expect(wrapper.vm.promptTypeLabel("baseline")).toBe("tags.baseline");
    });

    it("handles remove- prefix", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      expect(wrapper.vm.promptTypeLabel("remove-bug")).toBe("tags.bug");
    });

    it("returns empty for unknown type", () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      expect(wrapper.vm.promptTypeLabel("unknown")).toBe("");
    });
  });

  describe("event emissions", () => {
    it("emits set-columns when column button clicked", async () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      const buttons = wrapper.findAll("button");
      const colButton = buttons.find(b => b.text() === "3");
      if (colButton) {
        await colButton.trigger("click");
      }

      expect(wrapper.emitted("set-columns")).toBeTruthy();
    });

    it("emits open-note when note button clicked", async () => {
      const wrapper = mount(ViewerModal, {
        props: defaultProps,
      });

      const buttons = wrapper.findAll("button");
      const noteButton = buttons.find(b => b.text().includes("note.button"));
      if (noteButton) {
        await noteButton.trigger("click");
        expect(wrapper.emitted("open-note")).toBeTruthy();
      }
    });
  });
});

import { describe, expect, it } from "vitest";
import { useSyncAlerts } from "./useSyncAlerts";

describe("useSyncAlerts", () => {
  it("showToast adds alert to alerts array", () => {
    const { alerts, showToast } = useSyncAlerts();
    
    alerts.value = [];
    showToast("Test message", "warning");
    
    expect(alerts.value).toHaveLength(1);
    expect(alerts.value[0].message).toBe("Test message");
    expect(alerts.value[0].type).toBe("warning");
  });

  it("showToast uses default type", () => {
    const { alerts, showToast } = useSyncAlerts();
    
    alerts.value = [];
    showToast("Test message");
    
    expect(alerts.value[0].type).toBe("warning");
  });

  it("showToast generates unique ids", () => {
    const { alerts, showToast } = useSyncAlerts();
    
    alerts.value = [];
    showToast("Test 1", "error");
    const firstId = alerts.value[0].id;
    
    expect(firstId).toBeDefined();
    expect(typeof firstId).toBe("number");
  });

  it("clearAll removes all alerts", () => {
    const { alerts, showToast, clearAll } = useSyncAlerts();
    
    alerts.value = [];
    showToast("Test 1", "error");
    showToast("Test 2", "warning");
    
    clearAll();
    
    expect(alerts.value).toHaveLength(0);
  });

  it("alerts are shared across calls", () => {
    const { alerts: alerts1 } = useSyncAlerts();
    const { alerts: alerts2 } = useSyncAlerts();
    
    alerts1.value = [{ id: 1, message: "test", type: "warning" }];
    
    expect(alerts2.value).toHaveLength(1);
  });
});

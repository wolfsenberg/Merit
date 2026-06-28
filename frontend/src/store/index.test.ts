import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore, useUIStore } from "./index";

describe("useAuthStore", () => {
  beforeEach(() => {
    useAuthStore.setState({ accessToken: null, user: null });
  });

  it("starts with no authentication", () => {
    const state = useAuthStore.getState();
    expect(state.accessToken).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated()).toBe(false);
  });

  it("sets auth state", () => {
    const { setAuth } = useAuthStore.getState();
    setAuth("token123", {
      id: "user-1",
      email: "test@example.com",
      fullName: "Test User",
      role: "recipient",
    });

    const state = useAuthStore.getState();
    expect(state.accessToken).toBe("token123");
    expect(state.user?.email).toBe("test@example.com");
    expect(state.isAuthenticated()).toBe(true);
  });

  it("clears auth state", () => {
    const { setAuth, clearAuth } = useAuthStore.getState();
    setAuth("token123", {
      id: "user-1",
      email: "test@example.com",
      fullName: "Test User",
      role: "recipient",
    });
    clearAuth();

    const state = useAuthStore.getState();
    expect(state.accessToken).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated()).toBe(false);
  });
});

describe("useUIStore", () => {
  beforeEach(() => {
    useUIStore.setState({ sidebarOpen: false });
  });

  it("starts with sidebar closed", () => {
    const state = useUIStore.getState();
    expect(state.sidebarOpen).toBe(false);
  });

  it("toggles sidebar", () => {
    const { toggleSidebar } = useUIStore.getState();
    toggleSidebar();
    expect(useUIStore.getState().sidebarOpen).toBe(true);
    toggleSidebar();
    expect(useUIStore.getState().sidebarOpen).toBe(false);
  });

  it("sets sidebar open state directly", () => {
    const { setSidebarOpen } = useUIStore.getState();
    setSidebarOpen(true);
    expect(useUIStore.getState().sidebarOpen).toBe(true);
  });
});

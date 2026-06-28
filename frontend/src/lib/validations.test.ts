import { describe, it, expect } from "vitest";
import { loginSchema, registerSchema, createProgramSchema } from "./validations";

describe("loginSchema", () => {
  it("validates a correct login input", () => {
    const result = loginSchema.safeParse({
      email: "user@example.com",
      password: "secret123",
    });
    expect(result.success).toBe(true);
  });

  it("rejects invalid email", () => {
    const result = loginSchema.safeParse({
      email: "not-an-email",
      password: "secret123",
    });
    expect(result.success).toBe(false);
  });

  it("rejects empty password", () => {
    const result = loginSchema.safeParse({
      email: "user@example.com",
      password: "",
    });
    expect(result.success).toBe(false);
  });
});

describe("registerSchema", () => {
  it("validates correct registration input", () => {
    const result = registerSchema.safeParse({
      email: "user@example.com",
      password: "longpass1",
      fullName: "John Doe",
      role: "recipient",
    });
    expect(result.success).toBe(true);
  });

  it("rejects short password", () => {
    const result = registerSchema.safeParse({
      email: "user@example.com",
      password: "short",
      fullName: "John Doe",
      role: "recipient",
    });
    expect(result.success).toBe(false);
  });

  it("rejects invalid role", () => {
    const result = registerSchema.safeParse({
      email: "user@example.com",
      password: "longpass1",
      fullName: "John Doe",
      role: "invalid_role",
    });
    expect(result.success).toBe(false);
  });
});

describe("createProgramSchema", () => {
  it("validates correct program input", () => {
    const result = createProgramSchema.safeParse({
      name: "Test Program",
      description: "A funding program",
      fundingAmountPerRecipient: 1000,
      maxRecipients: 10,
      startDate: "2025-01-01T00:00:00.000Z",
    });
    expect(result.success).toBe(true);
  });

  it("rejects zero funding amount", () => {
    const result = createProgramSchema.safeParse({
      name: "Test Program",
      description: "A funding program",
      fundingAmountPerRecipient: 0,
      maxRecipients: 10,
      startDate: "2025-01-01T00:00:00.000Z",
    });
    expect(result.success).toBe(false);
  });

  it("rejects end date before start date", () => {
    const result = createProgramSchema.safeParse({
      name: "Test Program",
      description: "A funding program",
      fundingAmountPerRecipient: 1000,
      maxRecipients: 10,
      startDate: "2025-06-01T00:00:00.000Z",
      endDate: "2025-01-01T00:00:00.000Z",
    });
    expect(result.success).toBe(false);
  });
});

import { z } from "zod";

/**
 * Zod schema validation utilities for forms and API payloads.
 * Schemas mirror the backend Pydantic models for type safety.
 */

export const emailSchema = z
  .string()
  .email("Please enter a valid email address");

export const passwordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters");

export const registerSchema = z.object({
  email: emailSchema,
  password: passwordSchema,
  fullName: z.string().min(1, "Full name is required"),
  role: z.enum(["super_admin", "org_admin", "recipient"]),
  organizationId: z.string().uuid().optional(),
});

export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, "Password is required"),
});

export const createProgramSchema = z
  .object({
    name: z.string().min(1, "Program name is required"),
    description: z.string().min(1, "Description is required"),
    fundingAmountPerRecipient: z
      .number()
      .positive("Funding amount must be greater than zero"),
    maxRecipients: z
      .number()
      .int()
      .min(1, "Must have at least 1 recipient"),
    startDate: z.string().datetime(),
    endDate: z.string().datetime().optional(),
  })
  .refine(
    (data) => {
      if (data.endDate) {
        return new Date(data.endDate) > new Date(data.startDate);
      }
      return true;
    },
    {
      message: "End date must be after start date",
      path: ["endDate"],
    }
  );

export type RegisterInput = z.infer<typeof registerSchema>;
export type LoginInput = z.infer<typeof loginSchema>;
export type CreateProgramInput = z.infer<typeof createProgramSchema>;

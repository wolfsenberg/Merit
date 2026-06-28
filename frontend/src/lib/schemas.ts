/**
 * Zod validation schemas for authentication forms.
 */

import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

export type LoginFormData = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  full_name: z.string().min(2, "Full name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  role: z.enum(["recipient", "org_admin"], {
    required_error: "Please select a role",
  }),
  organization_id: z.string().optional(),
}).refine(
  (data) => {
    if (data.role === "org_admin" && (!data.organization_id || data.organization_id.trim() === "")) {
      return false;
    }
    return true;
  },
  {
    message: "Organization ID is required for Organization Admin role",
    path: ["organization_id"],
  }
);

export type RegisterFormData = z.infer<typeof registerSchema>;

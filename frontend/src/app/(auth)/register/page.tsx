"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { registerSchema, type RegisterFormData } from "@/lib/schemas";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<RegisterFormData>({
    full_name: "", email: "", password: "", role: "recipient", organization_id: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setApiError(null);

    const result = registerSchema.safeParse(formData);
    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      result.error.issues.forEach((issue) => {
        const path = issue.path[0] as string;
        fieldErrors[path] = issue.message;
      });
      setErrors(fieldErrors);
      return;
    }

    setIsLoading(true);
    try {
      const payload = { ...result.data, organization_id: result.data.role === "org_admin" ? result.data.organization_id : undefined };
      const response = await fetch("/api/v1/auth/register", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
      });
      if (!response.ok) { const data = await response.json(); setApiError(data.detail || "Registration failed"); return; }
      router.push("/login?registered=true");
    } catch { setApiError("Connection error. Please try again."); } finally { setIsLoading(false); }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-amber-50 via-white to-amber-50/30 px-4 py-8">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-amber-200/20 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full bg-amber-100/30 blur-3xl" />
      </div>

      <div className="relative w-full max-w-sm space-y-6">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-500 to-amber-600 shadow-lg shadow-amber-500/25">
            <span className="text-xl font-bold text-white">M</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Create your account</h1>
          <p className="mt-1 text-sm text-gray-500">Join the Merit funding platform</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {apiError && (
            <div className="rounded-xl bg-red-50 border border-red-100 p-3.5 text-sm text-red-700" role="alert">{apiError}</div>
          )}

          <div className="space-y-1.5">
            <Label htmlFor="full_name" className="text-sm font-medium text-gray-700">Full Name</Label>
            <Input id="full_name" placeholder="Juan Dela Cruz" value={formData.full_name} onChange={(e) => setFormData(p => ({...p, full_name: e.target.value}))} className="h-11 rounded-xl border-gray-200 bg-white/80 backdrop-blur-sm focus:border-amber-400 focus:ring-amber-400/20" />
            {errors.full_name && <p className="text-xs text-red-500">{errors.full_name}</p>}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="email" className="text-sm font-medium text-gray-700">Email</Label>
            <Input id="email" type="email" placeholder="you@example.com" value={formData.email} onChange={(e) => setFormData(p => ({...p, email: e.target.value}))} className="h-11 rounded-xl border-gray-200 bg-white/80 backdrop-blur-sm focus:border-amber-400 focus:ring-amber-400/20" />
            {errors.email && <p className="text-xs text-red-500">{errors.email}</p>}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="password" className="text-sm font-medium text-gray-700">Password</Label>
            <Input id="password" type="password" placeholder="Min 8 characters" value={formData.password} onChange={(e) => setFormData(p => ({...p, password: e.target.value}))} className="h-11 rounded-xl border-gray-200 bg-white/80 backdrop-blur-sm focus:border-amber-400 focus:ring-amber-400/20" />
            {errors.password && <p className="text-xs text-red-500">{errors.password}</p>}
          </div>

          <div className="space-y-1.5">
            <Label className="text-sm font-medium text-gray-700">I am a...</Label>
            <div className="grid grid-cols-2 gap-3">
              <button type="button" onClick={() => setFormData(p => ({...p, role: "recipient"}))}
                className={`rounded-xl border-2 p-3 text-center text-sm font-medium transition-all ${formData.role === "recipient" ? "border-amber-500 bg-amber-50 text-amber-700" : "border-gray-200 text-gray-600 hover:border-gray-300"}`}>
                <span className="block text-lg mb-1">🎓</span>Recipient
              </button>
              <button type="button" onClick={() => setFormData(p => ({...p, role: "org_admin"}))}
                className={`rounded-xl border-2 p-3 text-center text-sm font-medium transition-all ${formData.role === "org_admin" ? "border-amber-500 bg-amber-50 text-amber-700" : "border-gray-200 text-gray-600 hover:border-gray-300"}`}>
                <span className="block text-lg mb-1">🏢</span>Org Admin
              </button>
            </div>
          </div>

          {formData.role === "org_admin" && (
            <div className="space-y-1.5 animate-in fade-in slide-in-from-top-2">
              <Label htmlFor="organization_id" className="text-sm font-medium text-gray-700">Organization ID</Label>
              <Input id="organization_id" placeholder="Your organization UUID" value={formData.organization_id} onChange={(e) => setFormData(p => ({...p, organization_id: e.target.value}))} className="h-11 rounded-xl border-gray-200 bg-white/80 backdrop-blur-sm focus:border-amber-400 focus:ring-amber-400/20" />
              {errors.organization_id && <p className="text-xs text-red-500">{errors.organization_id}</p>}
            </div>
          )}

          <Button type="submit" className="w-full h-11 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white font-semibold shadow-md shadow-amber-500/20 transition-all" disabled={isLoading}>
            {isLoading ? "Creating account..." : "Create account"}
          </Button>
        </form>

        <p className="text-center text-sm text-gray-500">
          Already have an account? <Link href="/login" className="font-semibold text-amber-600 hover:text-amber-700">Sign in</Link>
        </p>
      </div>
    </div>
  );
}

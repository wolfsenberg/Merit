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
  const [formData, setFormData] = useState<RegisterFormData>({ full_name: "", email: "", password: "", role: "recipient", organization_id: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({}); setApiError(null);
    const result = registerSchema.safeParse(formData);
    if (!result.success) { const fe: Record<string, string> = {}; result.error.issues.forEach((i) => { fe[i.path[0] as string] = i.message; }); setErrors(fe); return; }
    setIsLoading(true);
    try {
      const payload = { ...result.data, organization_id: result.data.role === "org_admin" ? result.data.organization_id : undefined };
      const response = await fetch("/api/v1/auth/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      if (!response.ok) { const data = await response.json(); setApiError(data.detail || "Registration failed"); return; }
      router.push("/login?registered=true");
    } catch { setApiError("Connection error. Please try again."); } finally { setIsLoading(false); }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-merit-cream px-4 py-8">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-32 -right-32 h-64 w-64 rounded-full bg-merit-peach/60 blur-3xl" />
        <div className="absolute -bottom-32 -left-32 h-64 w-64 rounded-full bg-merit-sky/20 blur-3xl" />
      </div>

      <div className="relative w-full max-w-sm space-y-6">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-merit-gold shadow-lg shadow-[#F4BA45]/30">
            <span className="text-2xl font-bold text-white">M</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Create your account</h1>
          <p className="mt-1 text-sm text-gray-500">Join the Merit funding platform</p>
        </div>

        <div className="rounded-2xl bg-white p-6 shadow-sm border border-[#FFECCF]/60">
          <form onSubmit={handleSubmit} className="space-y-4">
            {apiError && <div className="rounded-xl bg-red-50 border border-red-100 p-3 text-sm text-red-700 animate-in">{apiError}</div>}

            <div className="space-y-1.5">
              <Label className="text-sm font-medium text-gray-700">Full Name</Label>
              <Input placeholder="Juan Dela Cruz" value={formData.full_name} onChange={(e) => setFormData(p => ({...p, full_name: e.target.value}))} className="h-11 rounded-xl border-gray-200 bg-merit-cream/50 focus:border-merit-gold focus:ring-[#F4BA45]/20" />
              {errors.full_name && <p className="text-xs text-red-500">{errors.full_name}</p>}
            </div>

            <div className="space-y-1.5">
              <Label className="text-sm font-medium text-gray-700">Email</Label>
              <Input type="email" placeholder="you@example.com" value={formData.email} onChange={(e) => setFormData(p => ({...p, email: e.target.value}))} className="h-11 rounded-xl border-gray-200 bg-merit-cream/50 focus:border-merit-gold focus:ring-[#F4BA45]/20" />
              {errors.email && <p className="text-xs text-red-500">{errors.email}</p>}
            </div>

            <div className="space-y-1.5">
              <Label className="text-sm font-medium text-gray-700">Password</Label>
              <Input type="password" placeholder="Min 8 characters" value={formData.password} onChange={(e) => setFormData(p => ({...p, password: e.target.value}))} className="h-11 rounded-xl border-gray-200 bg-merit-cream/50 focus:border-merit-gold focus:ring-[#F4BA45]/20" />
              {errors.password && <p className="text-xs text-red-500">{errors.password}</p>}
            </div>

            <div className="space-y-1.5">
              <Label className="text-sm font-medium text-gray-700">I am a...</Label>
              <div className="grid grid-cols-2 gap-3">
                <button type="button" onClick={() => setFormData(p => ({...p, role: "recipient"}))}
                  className={`rounded-xl border-2 p-3 text-center text-sm font-medium transition-all ${formData.role === "recipient" ? "border-merit-gold bg-merit-peach text-gold-700" : "border-gray-200 text-gray-600 hover:border-merit-peach"}`}>
                  <span className="block text-lg mb-1">🎓</span>Recipient
                </button>
                <button type="button" onClick={() => setFormData(p => ({...p, role: "org_admin"}))}
                  className={`rounded-xl border-2 p-3 text-center text-sm font-medium transition-all ${formData.role === "org_admin" ? "border-merit-gold bg-merit-peach text-gold-700" : "border-gray-200 text-gray-600 hover:border-merit-peach"}`}>
                  <span className="block text-lg mb-1">🏢</span>Org Admin
                </button>
              </div>
            </div>

            {formData.role === "org_admin" && (
              <div className="space-y-1.5 animate-in">
                <Label className="text-sm font-medium text-gray-700">Organization ID</Label>
                <Input placeholder="Your organization UUID" value={formData.organization_id} onChange={(e) => setFormData(p => ({...p, organization_id: e.target.value}))} className="h-11 rounded-xl border-gray-200 bg-merit-cream/50 focus:border-merit-gold focus:ring-[#F4BA45]/20" />
                {errors.organization_id && <p className="text-xs text-red-500">{errors.organization_id}</p>}
              </div>
            )}

            <Button type="submit" disabled={isLoading} className="w-full h-11 rounded-xl bg-merit-gold hover:bg-gold-500 text-white font-semibold shadow-md shadow-[#F4BA45]/25 transition-all">
              {isLoading ? "Creating account..." : "Create account"}
            </Button>
          </form>
        </div>

        <p className="text-center text-sm text-gray-500">
          Already have an account? <Link href="/login" className="font-semibold text-merit-gold hover:text-gold-600">Sign in</Link>
        </p>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { registerSchema, type RegisterFormData } from "@/lib/schemas";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { GraduationCap, Building2 } from "lucide-react";

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
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#FAFAF9] px-4 py-8">
      <div className="w-full max-w-[360px] space-y-6">
        <div className="text-center">
          <img src="/logo.svg" alt="Merit" className="mx-auto h-14 w-14 mb-5" />
          <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Create account</h1>
          <p className="mt-1.5 text-[13px] text-gray-400">Get started with Merit</p>
        </div>

        <div className="rounded-2xl border border-black/[0.06] bg-white p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
          <form onSubmit={handleSubmit} className="space-y-4">
            {apiError && <div className="rounded-lg bg-red-50 border border-red-100 px-3 py-2.5 text-[13px] text-red-600">{apiError}</div>}

            <div className="space-y-1.5">
              <Label className="text-[12px] font-medium text-gray-500 uppercase tracking-wide">Full Name</Label>
              <Input placeholder="Your full name" value={formData.full_name} onChange={(e) => setFormData(p => ({...p, full_name: e.target.value}))} className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[14px] placeholder:text-gray-300 focus:border-merit-gold focus:ring-1 focus:ring-merit-gold/20" />
              {errors.full_name && <p className="text-[11px] text-red-500">{errors.full_name}</p>}
            </div>

            <div className="space-y-1.5">
              <Label className="text-[12px] font-medium text-gray-500 uppercase tracking-wide">Email</Label>
              <Input type="email" placeholder="you@example.com" value={formData.email} onChange={(e) => setFormData(p => ({...p, email: e.target.value}))} className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[14px] placeholder:text-gray-300 focus:border-merit-gold focus:ring-1 focus:ring-merit-gold/20" />
              {errors.email && <p className="text-[11px] text-red-500">{errors.email}</p>}
            </div>

            <div className="space-y-1.5">
              <Label className="text-[12px] font-medium text-gray-500 uppercase tracking-wide">Password</Label>
              <Input type="password" placeholder="Min 8 characters" value={formData.password} onChange={(e) => setFormData(p => ({...p, password: e.target.value}))} className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[14px] placeholder:text-gray-300 focus:border-merit-gold focus:ring-1 focus:ring-merit-gold/20" />
              {errors.password && <p className="text-[11px] text-red-500">{errors.password}</p>}
            </div>

            <div className="space-y-2">
              <Label className="text-[12px] font-medium text-gray-500 uppercase tracking-wide">Role</Label>
              <div className="grid grid-cols-2 gap-2.5">
                <button type="button" onClick={() => setFormData(p => ({...p, role: "recipient"}))}
                  className={`flex flex-col items-center gap-1.5 rounded-xl border-2 p-3 transition-all duration-150 ${formData.role === "recipient" ? "border-merit-gold bg-merit-gold/5" : "border-black/[0.06] hover:border-black/10"}`}>
                  <GraduationCap className={`h-5 w-5 ${formData.role === "recipient" ? "text-merit-gold" : "text-gray-400"}`} strokeWidth={1.5} />
                  <span className={`text-[12px] font-medium ${formData.role === "recipient" ? "text-gray-900" : "text-gray-500"}`}>Recipient</span>
                </button>
                <button type="button" onClick={() => setFormData(p => ({...p, role: "org_admin"}))}
                  className={`flex flex-col items-center gap-1.5 rounded-xl border-2 p-3 transition-all duration-150 ${formData.role === "org_admin" ? "border-merit-gold bg-merit-gold/5" : "border-black/[0.06] hover:border-black/10"}`}>
                  <Building2 className={`h-5 w-5 ${formData.role === "org_admin" ? "text-merit-gold" : "text-gray-400"}`} strokeWidth={1.5} />
                  <span className={`text-[12px] font-medium ${formData.role === "org_admin" ? "text-gray-900" : "text-gray-500"}`}>Organization</span>
                </button>
              </div>
            </div>

            {formData.role === "org_admin" && (
              <div className="space-y-1.5 animate-in">
                <Label className="text-[12px] font-medium text-gray-500 uppercase tracking-wide">Organization ID</Label>
                <Input placeholder="UUID of your organization" value={formData.organization_id} onChange={(e) => setFormData(p => ({...p, organization_id: e.target.value}))} className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[14px] placeholder:text-gray-300 focus:border-merit-gold focus:ring-1 focus:ring-merit-gold/20" />
                {errors.organization_id && <p className="text-[11px] text-red-500">{errors.organization_id}</p>}
              </div>
            )}

            <Button type="submit" disabled={isLoading} className="w-full h-10 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-[13px] font-medium transition-all">
              {isLoading ? "Creating account..." : "Create account"}
            </Button>
          </form>
        </div>

        <p className="text-center text-[13px] text-gray-400">
          Already have an account? <Link href="/login" className="font-medium text-gray-900 hover:text-merit-gold transition-colors">Sign in</Link>
        </p>
      </div>
    </div>
  );
}

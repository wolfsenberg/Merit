"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { loginSchema, type LoginFormData } from "@/lib/schemas";
import { setTokens, setUser } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Play } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<LoginFormData>({ email: "", password: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDemoLoading, setIsDemoLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({}); setApiError(null);
    const result = loginSchema.safeParse(formData);
    if (!result.success) { const fe: Record<string, string> = {}; result.error.issues.forEach((i) => { fe[i.path[0] as string] = i.message; }); setErrors(fe); return; }
    setIsLoading(true);
    try {
      const response = await fetch("/api/v1/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(result.data) });
      if (!response.ok) { const data = await response.json(); setApiError(data.detail || "Invalid credentials"); return; }
      const tokens = await response.json();
      setTokens(tokens);
      try { const payload = JSON.parse(atob(tokens.access_token.split(".")[1])); setUser({ id: payload.sub, email: formData.email, full_name: payload.full_name || "", role: payload.role, organization_id: payload.organization_id }); } catch {}
      router.push("/dashboard");
    } catch { setApiError("Connection error. Please try again."); } finally { setIsLoading(false); }
  };

  const handleDemo = async () => {
    setIsDemoLoading(true);
    setApiError(null);

    const demoEmail = "demo@merit.app";
    const demoPassword = "demo12345";

    try {
      // Try to register the demo user (ignore if already exists)
      await fetch("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: demoEmail, password: demoPassword, full_name: "Demo User", role: "recipient" }),
      });

      // Login as demo user
      const response = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: demoEmail, password: demoPassword }),
      });

      if (!response.ok) {
        setApiError("Demo is temporarily unavailable. Try again.");
        return;
      }

      const tokens = await response.json();
      setTokens(tokens);
      setUser({ id: "demo-user", email: demoEmail, full_name: "Demo User", role: "recipient" });
      router.push("/dashboard");
    } catch {
      setApiError("Connection error. Make sure the backend is running.");
    } finally {
      setIsDemoLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#FAFAF9] px-4">
      <div className="w-full max-w-[360px] space-y-8">
        {/* Logo */}
        <div className="text-center">
          <img src="/logo.svg" alt="Merit" className="mx-auto h-14 w-14 mb-5" />
          <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Sign in</h1>
          <p className="mt-1.5 text-[13px] text-gray-400">Welcome back to Merit</p>
        </div>

        {/* Form */}
        <div className="rounded-2xl border border-black/[0.06] bg-white p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
          <form onSubmit={handleSubmit} className="space-y-4">
            {apiError && (
              <div className="rounded-lg bg-red-50 border border-red-100 px-3 py-2.5 text-[13px] text-red-600">{apiError}</div>
            )}

            <div className="space-y-1.5">
              <Label className="text-[12px] font-medium text-gray-500 uppercase tracking-wide">Email</Label>
              <Input
                type="email" placeholder="you@example.com"
                value={formData.email} onChange={(e) => setFormData(p => ({...p, email: e.target.value}))}
                className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[14px] placeholder:text-gray-300 focus:border-merit-gold focus:ring-1 focus:ring-merit-gold/20"
              />
              {errors.email && <p className="text-[11px] text-red-500">{errors.email}</p>}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label className="text-[12px] font-medium text-gray-500 uppercase tracking-wide">Password</Label>
                <button type="button" className="text-[11px] text-gray-400 hover:text-merit-gold transition-colors">Forgot?</button>
              </div>
              <Input
                type="password" placeholder="Enter password"
                value={formData.password} onChange={(e) => setFormData(p => ({...p, password: e.target.value}))}
                className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[14px] placeholder:text-gray-300 focus:border-merit-gold focus:ring-1 focus:ring-merit-gold/20"
              />
              {errors.password && <p className="text-[11px] text-red-500">{errors.password}</p>}
            </div>

            <Button type="submit" disabled={isLoading}
              className="w-full h-10 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-[13px] font-medium transition-all">
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  Signing in
                </span>
              ) : "Sign in"}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative my-5">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-black/[0.06]" /></div>
            <div className="relative flex justify-center"><span className="bg-white px-3 text-[11px] text-gray-400">or</span></div>
          </div>

          {/* Demo button */}
          <Button
            type="button"
            onClick={handleDemo}
            disabled={isDemoLoading}
            className="w-full h-10 rounded-lg bg-merit-gold/10 hover:bg-merit-gold/20 text-gray-900 text-[13px] font-medium border border-merit-gold/20 transition-all"
            variant="ghost"
          >
            {isDemoLoading ? (
              <span className="flex items-center gap-2">
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-merit-gold/30 border-t-merit-gold" />
                Loading demo...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Play className="h-3.5 w-3.5 text-merit-gold" fill="currentColor" />
                Try Demo
              </span>
            )}
          </Button>
        </div>

        <p className="text-center text-[13px] text-gray-400">
          New to Merit? <Link href="/register" className="font-medium text-gray-900 hover:text-merit-gold transition-colors">Create an account</Link>
        </p>
      </div>
    </div>
  );
}

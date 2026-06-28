"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { loginSchema, type LoginFormData } from "@/lib/schemas";
import { setTokens, setUser } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<LoginFormData>({ email: "", password: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setApiError(null);

    const result = loginSchema.safeParse(formData);
    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      result.error.issues.forEach((issue) => { fieldErrors[issue.path[0] as string] = issue.message; });
      setErrors(fieldErrors);
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch("/api/v1/auth/login", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(result.data),
      });
      if (!response.ok) { const data = await response.json(); setApiError(data.detail || "Invalid credentials"); return; }
      const tokens = await response.json();
      setTokens(tokens);
      try {
        const payload = JSON.parse(atob(tokens.access_token.split(".")[1]));
        setUser({ id: payload.sub, email: formData.email, full_name: payload.full_name || "", role: payload.role, organization_id: payload.organization_id });
      } catch {}
      router.push("/dashboard");
    } catch { setApiError("Connection error. Please try again."); } finally { setIsLoading(false); }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-merit-cream px-4">
      {/* Background decoration */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-32 -right-32 h-64 w-64 rounded-full bg-merit-peach/60 blur-3xl" />
        <div className="absolute -bottom-32 -left-32 h-64 w-64 rounded-full bg-merit-sky/20 blur-3xl" />
        <div className="absolute top-1/3 left-1/4 h-48 w-48 rounded-full bg-merit-gold/10 blur-3xl" />
      </div>

      <div className="relative w-full max-w-sm space-y-8">
        {/* Logo */}
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-merit-gold shadow-lg shadow-[#F4BA45]/30">
            <span className="text-2xl font-bold text-white">M</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Welcome back</h1>
          <p className="mt-1 text-sm text-gray-500">Sign in to your Merit account</p>
        </div>

        {/* Form card */}
        <div className="rounded-2xl bg-white p-6 shadow-sm border border-[#FFECCF]/60">
          <form onSubmit={handleSubmit} className="space-y-5">
            {apiError && (
              <div className="rounded-xl bg-red-50 border border-red-100 p-3 text-sm text-red-700 animate-in">{apiError}</div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-sm font-medium text-gray-700">Email</Label>
              <Input
                id="email" type="email" placeholder="you@example.com"
                value={formData.email} onChange={(e) => setFormData(p => ({...p, email: e.target.value}))}
                className="h-11 rounded-xl border-gray-200 bg-merit-cream/50 focus:border-merit-gold focus:ring-[#F4BA45]/20"
              />
              {errors.email && <p className="text-xs text-red-500">{errors.email}</p>}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-sm font-medium text-gray-700">Password</Label>
                <button type="button" className="text-xs text-merit-gold hover:text-gold-600 font-medium">Forgot?</button>
              </div>
              <Input
                id="password" type="password" placeholder="••••••••"
                value={formData.password} onChange={(e) => setFormData(p => ({...p, password: e.target.value}))}
                className="h-11 rounded-xl border-gray-200 bg-merit-cream/50 focus:border-merit-gold focus:ring-[#F4BA45]/20"
              />
              {errors.password && <p className="text-xs text-red-500">{errors.password}</p>}
            </div>

            <Button
              type="submit" disabled={isLoading}
              className="w-full h-11 rounded-xl bg-merit-gold hover:bg-gold-500 text-white font-semibold shadow-md shadow-[#F4BA45]/25 transition-all hover:shadow-lg hover:shadow-[#F4BA45]/35"
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Signing in...
                </span>
              ) : "Sign in"}
            </Button>
          </form>
        </div>

        <p className="text-center text-sm text-gray-500">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="font-semibold text-merit-gold hover:text-gold-600">Create one</Link>
        </p>
      </div>
    </div>
  );
}

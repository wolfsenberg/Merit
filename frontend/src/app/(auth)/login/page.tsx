"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { loginSchema, type LoginFormData } from "@/lib/schemas";
import { setTokens, setUser } from "@/lib/auth";
import { connectFreighter, isFreighterInstalled, getCachedPublicKey, disconnectFreighter } from "@/lib/freighter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Play, Wallet, ExternalLink, CheckCircle2 } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<LoginFormData>({ email: "", password: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDemoLoading, setIsDemoLoading] = useState(false);

  // Freighter state
  const [freighterInstalled, setFreighterInstalled] = useState<boolean | null>(null);
  const [walletConnected, setWalletConnected] = useState(false);
  const [publicKey, setPublicKey] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

  useEffect(() => {
    // Check Freighter status on mount
    (async () => {
      const installed = await isFreighterInstalled();
      setFreighterInstalled(installed);
      const cachedKey = getCachedPublicKey();
      if (cachedKey) {
        setWalletConnected(true);
        setPublicKey(cachedKey);
      }
    })();
  }, []);

  const handleConnectWallet = async () => {
    setIsConnecting(true);
    setApiError(null);
    const key = await connectFreighter();
    if (key) {
      setWalletConnected(true);
      setPublicKey(key);
    } else {
      setApiError("Wallet connection was denied or failed. Please try again.");
    }
    setIsConnecting(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!walletConnected) { setApiError("Please connect your Freighter wallet first."); return; }
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
    if (!walletConnected) { setApiError("Please connect your Freighter wallet first."); return; }
    setIsDemoLoading(true); setApiError(null);
    const demoEmail = "demo@merit.app";
    const demoPassword = "demo12345";
    try {
      await fetch("/api/v1/auth/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: demoEmail, password: demoPassword, full_name: "Demo User", role: "recipient" }) });
      const response = await fetch("/api/v1/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: demoEmail, password: demoPassword }) });
      if (!response.ok) { setApiError("Demo temporarily unavailable."); return; }
      const tokens = await response.json();
      setTokens(tokens);
      setUser({ id: "demo-user", email: demoEmail, full_name: "Demo User", role: "recipient" });
      router.push("/dashboard");
    } catch { setApiError("Connection error. Make sure the backend is running."); } finally { setIsDemoLoading(false); }
  };

  const handleAdminDemo = async () => {
    if (!walletConnected) { setApiError("Please connect your Freighter wallet first."); return; }
    setIsDemoLoading(true); setApiError(null);
    const adminEmail = "admin@merit.app";
    const adminPassword = "admin12345";
    try {
      await fetch("/api/v1/auth/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: adminEmail, password: adminPassword, full_name: "DOST Admin", role: "org_admin", organization_id: "00000000-0000-0000-0000-000000000001" }) });
      const response = await fetch("/api/v1/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: adminEmail, password: adminPassword }) });
      if (!response.ok) { setApiError("Admin demo temporarily unavailable."); return; }
      const tokens = await response.json();
      setTokens(tokens);
      setUser({ id: "admin-demo", email: adminEmail, full_name: "DOST Admin", role: "org_admin", organization_id: "00000000-0000-0000-0000-000000000001" });
      router.push("/dashboard");
    } catch { setApiError("Connection error. Make sure the backend is running."); } finally { setIsDemoLoading(false); }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#FAFAF9] px-4">
      <div className="w-full max-w-[360px] space-y-8">
        {/* Logo */}
        <div className="text-center">
          <img src="/logo.svg" alt="Merit" className="mx-auto h-14 w-14 mb-5" />
          <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Sign in</h1>
          <p className="mt-1.5 text-[13px] text-gray-400">Connect wallet and access Merit</p>
        </div>

        <div className="rounded-2xl border border-black/[0.06] bg-white p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
          {/* Step 1: Connect Wallet */}
          <div className="mb-5">
            <div className="flex items-center gap-2 mb-3">
              <span className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${walletConnected ? "bg-emerald-500 text-white" : "bg-gray-200 text-gray-500"}`}>
                {walletConnected ? <CheckCircle2 className="h-3 w-3" /> : "1"}
              </span>
              <span className="text-[12px] font-medium text-gray-500 uppercase tracking-wide">Connect Wallet</span>
            </div>

            {freighterInstalled === false ? (
              <a href="https://www.freighter.app" target="_blank" rel="noopener noreferrer"
                className="flex items-center justify-between rounded-lg border border-black/[0.06] bg-[#FAFAF9] p-3 hover:border-merit-gold/30 transition-colors">
                <div>
                  <p className="text-[13px] font-medium text-gray-900">Install Freighter</p>
                  <p className="text-[11px] text-gray-400">Browser extension required</p>
                </div>
                <ExternalLink className="h-4 w-4 text-gray-400" />
              </a>
            ) : walletConnected ? (
              <div className="flex items-center gap-3 rounded-lg border border-emerald-100 bg-emerald-50/50 p-3">
                <Wallet className="h-4 w-4 text-emerald-600" strokeWidth={1.8} />
                <div className="flex-1 min-w-0">
                  <p className="text-[12px] font-medium text-emerald-700">Connected</p>
                  <p className="text-[11px] text-emerald-600/70 font-mono truncate">{publicKey?.slice(0, 8)}...{publicKey?.slice(-6)}</p>
                </div>
              </div>
            ) : (
              <Button
                type="button"
                onClick={handleConnectWallet}
                disabled={isConnecting}
                className="w-full h-10 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-[13px] font-medium"
              >
                {isConnecting ? (
                  <span className="flex items-center gap-2">
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    Connecting...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Wallet className="h-4 w-4" strokeWidth={1.8} />
                    Connect Freighter
                  </span>
                )}
              </Button>
            )}
          </div>

          {/* Step 2: Login Form */}
          <div className={`transition-opacity duration-200 ${walletConnected ? "opacity-100" : "opacity-40 pointer-events-none"}`}>
            <div className="flex items-center gap-2 mb-3">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-gray-200 text-[10px] font-bold text-gray-500">2</span>
              <span className="text-[12px] font-medium text-gray-500 uppercase tracking-wide">Sign In</span>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3">
              {apiError && (
                <div className="rounded-lg bg-red-50 border border-red-100 px-3 py-2.5 text-[13px] text-red-600">{apiError}</div>
              )}

              <div className="space-y-1.5">
                <Label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Email</Label>
                <Input type="email" placeholder="you@example.com" value={formData.email} onChange={(e) => setFormData(p => ({...p, email: e.target.value}))}
                  className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[14px] placeholder:text-gray-300 focus:border-merit-gold focus:ring-1 focus:ring-merit-gold/20" />
                {errors.email && <p className="text-[11px] text-red-500">{errors.email}</p>}
              </div>

              <div className="space-y-1.5">
                <Label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Password</Label>
                <Input type="password" placeholder="Enter password" value={formData.password} onChange={(e) => setFormData(p => ({...p, password: e.target.value}))}
                  className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[14px] placeholder:text-gray-300 focus:border-merit-gold focus:ring-1 focus:ring-merit-gold/20" />
                {errors.password && <p className="text-[11px] text-red-500">{errors.password}</p>}
              </div>

              <Button type="submit" disabled={isLoading || !walletConnected}
                className="w-full h-10 rounded-lg bg-merit-gold hover:bg-gold-500 text-white text-[13px] font-medium shadow-sm shadow-merit-gold/20 transition-all">
                {isLoading ? "Signing in..." : "Sign in"}
              </Button>
            </form>

            {/* Divider */}
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-black/[0.06]" /></div>
              <div className="relative flex justify-center"><span className="bg-white px-3 text-[11px] text-gray-400">or</span></div>
            </div>

            {/* Demo buttons */}
            <div className="grid grid-cols-2 gap-2">
              <Button type="button" onClick={handleDemo} disabled={isDemoLoading || !walletConnected} variant="ghost"
                className="h-10 rounded-lg bg-merit-gold/10 hover:bg-merit-gold/20 text-gray-900 text-[12px] font-medium border border-merit-gold/20 transition-all">
                {isDemoLoading ? "Loading..." : (
                  <span className="flex items-center gap-1.5"><Play className="h-3 w-3 text-merit-gold" fill="currentColor" />Student Demo</span>
                )}
              </Button>
              <Button type="button" onClick={handleAdminDemo} disabled={isDemoLoading || !walletConnected} variant="ghost"
                className="h-10 rounded-lg bg-gray-900/5 hover:bg-gray-900/10 text-gray-900 text-[12px] font-medium border border-black/[0.06] transition-all">
                {isDemoLoading ? "Loading..." : (
                  <span className="flex items-center gap-1.5"><Play className="h-3 w-3 text-gray-600" fill="currentColor" />Admin Demo</span>
                )}
              </Button>
            </div>
          </div>
        </div>

        <p className="text-center text-[13px] text-gray-400">
          New to Merit? <Link href="/register" className="font-medium text-gray-900 hover:text-merit-gold transition-colors">Create an account</Link>
        </p>
      </div>
    </div>
  );
}

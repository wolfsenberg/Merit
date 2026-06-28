"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { clearTokens, getUser } from "@/lib/auth";
import { disconnectFreighter, getCachedPublicKey } from "@/lib/freighter";
import { Menu, LogOut, Wallet } from "lucide-react";

interface HeaderProps { onMenuToggle: () => void; }

export function Header({ onMenuToggle }: HeaderProps) {
  const router = useRouter();
  const user = getUser();
  const walletKey = getCachedPublicKey();

  const handleLogout = () => {
    clearTokens();
    disconnectFreighter();
    router.push("/login");
  };  return (
    <header className="sticky top-0 z-30 flex h-[52px] items-center bg-white/80 backdrop-blur-xl border-b border-black/[0.04] px-4 md:px-6">
      <button className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-500 hover:bg-black/[0.04] md:hidden" onClick={onMenuToggle} aria-label="Menu">
        <Menu className="h-[18px] w-[18px]" strokeWidth={1.8} />
      </button>

      <Link href="/dashboard" className="flex items-center gap-2 md:hidden ml-2">
        <img src="/logo.svg" alt="Merit" className="h-6 w-6" />
        <span className="text-[15px] font-semibold text-gray-900">Merit</span>
      </Link>

      <div className="flex-1" />

      <div className="flex items-center gap-3">
        {walletKey && (
          <div className="hidden md:flex items-center gap-1.5 rounded-md bg-emerald-50 border border-emerald-100 px-2 py-1">
            <Wallet className="h-3 w-3 text-emerald-600" strokeWidth={1.8} />
            <span className="text-[11px] font-mono text-emerald-700">{walletKey.slice(0, 4)}...{walletKey.slice(-4)}</span>
          </div>
        )}
        <span className="hidden md:block text-[13px] text-gray-500">{user?.full_name || user?.email}</span>
        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-merit-gold to-[#E5A830] text-[10px] font-semibold text-white">
          {user?.full_name?.charAt(0)?.toUpperCase() || "U"}
        </div>
        <button onClick={handleLogout} className="flex h-7 w-7 items-center justify-center rounded-lg text-gray-400 hover:bg-black/[0.04] hover:text-gray-600" aria-label="Sign out">
          <LogOut className="h-[15px] w-[15px]" strokeWidth={1.8} />
        </button>
      </div>
    </header>
  );
}

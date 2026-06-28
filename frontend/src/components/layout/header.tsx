"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { clearTokens, getUser } from "@/lib/auth";
import { disconnectFreighter, getCachedPublicKey } from "@/lib/freighter";
import { Menu, LogOut, Wallet, Info, X, ChevronRight, ChevronLeft, FileCheck, Zap, Shield, Banknote } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface HeaderProps { onMenuToggle: () => void; }

// Onboarding slides data
const slides: { icon: LucideIcon; title: string; desc: string; highlight: string }[] = [
  { icon: Zap, title: "No more long queues", desc: "Your scholarship organization handles verification. You just accept the funds directly in the app — no windows, no waiting.", highlight: "Apply from anywhere, anytime." },
  { icon: FileCheck, title: "Receive funds instantly", desc: "Once verified by your scholarship provider, funds land in your Merit wallet immediately. Like GCash, but for scholars.", highlight: "No more delayed stipends." },
  { icon: Shield, title: "Built-in savings goals", desc: "Set goals like 'Laptop Fund' or 'Emergency'. Lock your money until you hit the target — discipline made easy.", highlight: "Your money works for you." },
  { icon: Banknote, title: "Cash out anytime", desc: "Transfer to GCash, bank account, or keep it in your Merit wallet. Powered by blockchain, but feels like any other app.", highlight: "No crypto knowledge needed." },
];

export function Header({ onMenuToggle }: HeaderProps) {
  const router = useRouter();
  const user = getUser();
  const walletKey = getCachedPublicKey();
  const [showInfo, setShowInfo] = useState(false);
  const [infoSlide, setInfoSlide] = useState(0);

  const handleLogout = () => {
    clearTokens();
    disconnectFreighter();
    router.push("/login");
  };

  const currentSlide = slides[infoSlide];
  const SlideIcon = currentSlide.icon;

  return (
    <>
      <header className="sticky top-0 z-30 flex h-[52px] items-center bg-white/80 backdrop-blur-xl border-b border-black/[0.04] px-4 md:px-6">
        <button className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-500 hover:bg-black/[0.04] md:hidden" onClick={onMenuToggle} aria-label="Menu">
          <Menu className="h-[18px] w-[18px]" strokeWidth={1.8} />
        </button>

        <Link href="/dashboard" className="flex items-center gap-2 ml-2 md:hidden">
          <img src="/logo.svg" alt="Merit" className="h-6 w-6" />
          <span className="text-[15px] font-semibold text-gray-900">Merit</span>
        </Link>
        <button onClick={() => { setShowInfo(true); setInfoSlide(0); }} className="ml-1 flex h-5 w-5 items-center justify-center rounded-full border border-black/[0.08] text-gray-400 hover:text-merit-gold hover:border-merit-gold/30 transition-colors md:hidden" aria-label="About Merit">
          <Info className="h-3 w-3" strokeWidth={2} />
        </button>

        <div className="flex-1" />

        <div className="flex items-center gap-2">
          {walletKey && (
            <div className="hidden md:flex items-center gap-1.5 rounded-md bg-emerald-50 border border-emerald-100 px-2 py-1">
              <Wallet className="h-3 w-3 text-emerald-600" strokeWidth={1.8} />
              <span className="text-[11px] font-mono text-emerald-700">{walletKey.slice(0, 4)}...{walletKey.slice(-4)}</span>
            </div>
          )}
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-merit-gold to-[#E5A830] text-[10px] font-semibold text-white">
            {user?.full_name?.charAt(0)?.toUpperCase() || "U"}
          </div>
          <button onClick={handleLogout} className="flex h-7 w-7 items-center justify-center rounded-lg text-gray-400 hover:bg-black/[0.04] hover:text-gray-600" aria-label="Sign out">
            <LogOut className="h-[15px] w-[15px]" strokeWidth={1.8} />
          </button>
        </div>
      </header>

      {/* Info modal overlay */}
      {showInfo && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => setShowInfo(false)}>
          <div className="w-[340px] max-h-[500px] rounded-2xl bg-white p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
            {/* Close */}
            <div className="flex justify-end mb-2">
              <button onClick={() => setShowInfo(false)} className="flex h-7 w-7 items-center justify-center rounded-full text-gray-400 hover:bg-gray-100">
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Slide content */}
            <div className="text-center px-2">
              <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-merit-gold/10 border border-merit-gold/20">
                <SlideIcon className="h-6 w-6 text-merit-gold" strokeWidth={1.5} />
              </div>
              <h2 className="text-[18px] font-semibold text-gray-900">{currentSlide.title}</h2>
              <p className="mt-3 text-[13px] text-gray-500 leading-relaxed">{currentSlide.desc}</p>
              <p className="mt-2 text-[12px] font-medium text-merit-gold">{currentSlide.highlight}</p>
            </div>

            {/* Navigation */}
            <div className="flex items-center justify-between mt-6">
              <button onClick={() => setInfoSlide(Math.max(0, infoSlide - 1))} disabled={infoSlide === 0}
                className="flex h-8 w-8 items-center justify-center rounded-full text-gray-400 hover:bg-gray-100 disabled:opacity-30">
                <ChevronLeft className="h-4 w-4" />
              </button>

              {/* Dots */}
              <div className="flex gap-1.5">
                {slides.map((_, i) => (
                  <div key={i} className={`h-1.5 rounded-full transition-all ${i === infoSlide ? "w-5 bg-merit-gold" : "w-1.5 bg-gray-200"}`} />
                ))}
              </div>

              <button onClick={() => { if (infoSlide < slides.length - 1) setInfoSlide(infoSlide + 1); else setShowInfo(false); }}
                className="flex h-8 w-8 items-center justify-center rounded-full text-gray-400 hover:bg-gray-100">
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

"use client";

import { getUser } from "@/lib/auth";
import { ArrowDownLeft, ArrowUpRight, PiggyBank, Wallet, Receipt, Search, TrendingUp, CheckCircle2, Bell } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const user = getUser();

  return (
    <div className="space-y-6">
      {/* Balance card — GCash style */}
      <div className="rounded-2xl bg-gradient-to-br from-gray-900 to-gray-800 p-5 text-white shadow-xl">
        <p className="text-[11px] font-medium text-white/50 uppercase tracking-wider">Available Balance</p>
        <p className="mt-1 text-[32px] font-bold tracking-tight">PHP 10,000<span className="text-[16px] text-white/40 font-normal">.00</span></p>
        <div className="mt-4 flex items-center gap-3">
          <Link href="/wallet" className="flex flex-col items-center gap-1">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 backdrop-blur-sm">
              <ArrowDownLeft className="h-4 w-4 text-emerald-400" strokeWidth={2} />
            </div>
            <span className="text-[10px] text-white/60">Receive</span>
          </Link>
          <Link href="/wallet/cashout" className="flex flex-col items-center gap-1">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 backdrop-blur-sm">
              <ArrowUpRight className="h-4 w-4 text-white/80" strokeWidth={2} />
            </div>
            <span className="text-[10px] text-white/60">Cash Out</span>
          </Link>
          <Link href="/savings" className="flex flex-col items-center gap-1">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 backdrop-blur-sm">
              <PiggyBank className="h-4 w-4 text-merit-gold" strokeWidth={2} />
            </div>
            <span className="text-[10px] text-white/60">Save</span>
          </Link>
        </div>
      </div>

      {/* Savings goal preview */}
      <Link href="/savings" className="block rounded-xl border border-merit-gold/20 bg-merit-gold/[0.04] p-4 transition-all hover:border-merit-gold/40">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <PiggyBank className="h-5 w-5 text-merit-gold" strokeWidth={1.5} />
            <div>
              <p className="text-[13px] font-medium text-gray-900">Laptop Fund</p>
              <p className="text-[11px] text-gray-400">PHP 3,500 of PHP 10,000</p>
            </div>
          </div>
          <span className="text-[12px] font-semibold text-merit-gold">35%</span>
        </div>
        <div className="mt-2 h-1.5 rounded-full bg-merit-gold/10 overflow-hidden">
          <div className="h-full rounded-full bg-merit-gold transition-all" style={{ width: "35%" }} />
        </div>
      </Link>

      {/* Quick actions */}
      <div className="grid grid-cols-4 gap-2">
        <QuickAction icon={<Search className="h-4 w-4" />} label="Scholarships" href="/programs/browse" />
        <QuickAction icon={<Receipt className="h-4 w-4" />} label="Transactions" href="/transactions" />
        <QuickAction icon={<PiggyBank className="h-4 w-4" />} label="Savings" href="/savings" />
        <QuickAction icon={<Bell className="h-4 w-4" />} label="Alerts" href="/notifications" />
      </div>

      {/* Active scholarship */}
      <div>
        <h2 className="text-[12px] font-medium text-gray-400 uppercase tracking-wider mb-3">Active Scholarship</h2>
        <div className="rounded-xl border border-black/[0.04] bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[13px] font-semibold text-gray-900">DOST-SEI Merit Scholarship</p>
              <p className="text-[11px] text-gray-400 mt-0.5">1st Semester 2026 — Verified</p>
            </div>
            <span className="flex items-center gap-1 text-[10px] font-medium text-emerald-600">
              <CheckCircle2 className="h-3 w-3" /> Active
            </span>
          </div>
          <div className="mt-3 flex items-center gap-4 text-[11px] text-gray-500">
            <span>Next payout: <strong className="text-gray-900">Dec 2026</strong></span>
            <span>Amount: <strong className="text-gray-900">PHP 10,000</strong></span>
          </div>
        </div>
      </div>

      {/* Recent */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[12px] font-medium text-gray-400 uppercase tracking-wider">Recent</h2>
          <Link href="/transactions" className="text-[11px] font-medium text-merit-gold">See all</Link>
        </div>
        <div className="rounded-xl border border-black/[0.04] bg-white overflow-hidden">
          <TxRow icon={<ArrowDownLeft className="h-4 w-4 text-emerald-500" />} title="Scholarship Received" sub="DOST-SEI Fund" amount="+ PHP 10,000" date="Jun 25" />
          <TxRow icon={<ArrowUpRight className="h-4 w-4 text-orange-500" />} title="Cash Out to GCash" sub="•••• 1234" amount="- PHP 5,000" date="Jun 27" />
          <TxRow icon={<PiggyBank className="h-4 w-4 text-merit-gold" />} title="Saved to Laptop Fund" sub="Goal: PHP 10,000" amount="- PHP 3,500" date="Jun 27" last />
        </div>
      </div>
    </div>
  );
}

function QuickAction({ icon, label, href }: { icon: React.ReactNode; label: string; href: string }) {
  return (
    <Link href={href} className="flex flex-col items-center gap-1.5 rounded-xl border border-black/[0.04] bg-white py-3 transition-all hover:border-merit-gold/20 hover:shadow-sm">
      <span className="text-gray-500">{icon}</span>
      <span className="text-[10px] font-medium text-gray-600">{label}</span>
    </Link>
  );
}

function TxRow({ icon, title, sub, amount, date, last }: { icon: React.ReactNode; title: string; sub: string; amount: string; date: string; last?: boolean }) {
  return (
    <div className={`flex items-center gap-3 px-4 py-3 ${!last ? "border-b border-black/[0.03]" : ""}`}>
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#FAFAF9] shrink-0">{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-[12px] font-medium text-gray-900">{title}</p>
        <p className="text-[10px] text-gray-400">{sub}</p>
      </div>
      <div className="text-right shrink-0">
        <p className={`text-[12px] font-semibold ${amount.startsWith("+") ? "text-emerald-600" : "text-gray-700"}`}>{amount}</p>
        <p className="text-[10px] text-gray-400">{date}</p>
      </div>
    </div>
  );
}

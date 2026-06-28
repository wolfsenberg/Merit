"use client";

import { Users, Banknote, TrendingUp, CheckCircle2, Clock, ArrowDownLeft } from "lucide-react";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Analytics</h1>
        <p className="mt-1 text-[13px] text-gray-400">Scholarship program performance overview</p>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <MetricCard label="Total Scholars" value="70" change="+12 this month" icon={<Users className="h-4 w-4" />} />
        <MetricCard label="Total Disbursed" value="PHP 750K" change="+PHP 120K" icon={<Banknote className="h-4 w-4" />} />
        <MetricCard label="Approval Rate" value="89%" change="+3%" icon={<CheckCircle2 className="h-4 w-4" />} />
        <MetricCard label="Avg Processing" value="2.4 days" change="-0.5 days" icon={<Clock className="h-4 w-4" />} />
      </div>

      {/* Disbursement breakdown */}
      <div className="rounded-xl border border-black/[0.04] bg-white p-5">
        <h3 className="text-[13px] font-medium text-gray-900 mb-4">Disbursement Breakdown</h3>
        <div className="space-y-3">
          <BarRow label="DOST-SEI Merit" amount="PHP 470,000" percent={63} />
          <BarRow label="CHED Tulong Dunong" amount="PHP 280,000" percent={37} />
        </div>
      </div>

      {/* Recent disbursements */}
      <div className="rounded-xl border border-black/[0.04] bg-white overflow-hidden">
        <div className="px-4 py-3 border-b border-black/[0.03]">
          <h3 className="text-[13px] font-medium text-gray-900">Recent Disbursements</h3>
        </div>
        <DisbursementRow name="Demo User" university="PUP Manila" amount="PHP 10,000" date="Jun 25" />
        <DisbursementRow name="Grace Lim" university="TUP Manila" amount="PHP 10,000" date="Jun 24" />
        <DisbursementRow name="Carlos Garcia" university="DLSU" amount="PHP 10,000" date="Jun 23" />
        <DisbursementRow name="Ana Cruz" university="Ateneo" amount="PHP 10,000" date="Jun 22" last />
      </div>
    </div>
  );
}

function MetricCard({ label, value, change, icon }: { label: string; value: string; change: string; icon: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-black/[0.04] bg-white p-4">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-medium text-gray-400 uppercase tracking-wide">{label}</span>
        <span className="text-gray-300">{icon}</span>
      </div>
      <p className="mt-1.5 text-[18px] font-semibold text-gray-900">{value}</p>
      <span className="text-[10px] font-medium text-emerald-500">{change}</span>
    </div>
  );
}

function BarRow({ label, amount, percent }: { label: string; amount: string; percent: number }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[12px] text-gray-700">{label}</span>
        <span className="text-[11px] font-medium text-gray-900">{amount}</span>
      </div>
      <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
        <div className="h-full rounded-full bg-merit-gold" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

function DisbursementRow({ name, university, amount, date, last }: { name: string; university: string; amount: string; date: string; last?: boolean }) {
  return (
    <div className={`flex items-center gap-3 px-4 py-3 ${!last ? "border-b border-black/[0.03]" : ""}`}>
      <ArrowDownLeft className="h-4 w-4 text-emerald-500 shrink-0" strokeWidth={1.8} />
      <div className="flex-1 min-w-0">
        <p className="text-[12px] font-medium text-gray-900">{name}</p>
        <p className="text-[10px] text-gray-400">{university}</p>
      </div>
      <div className="text-right shrink-0">
        <p className="text-[12px] font-semibold text-emerald-600">{amount}</p>
        <p className="text-[10px] text-gray-400">{date}</p>
      </div>
    </div>
  );
}

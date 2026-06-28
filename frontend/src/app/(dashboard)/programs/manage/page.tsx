"use client";

import { useState } from "react";
import Link from "next/link";
import { Users, Banknote, CheckCircle2, Clock, ArrowUpRight, FileText } from "lucide-react";

interface Program {
  id: string;
  name: string;
  totalScholars: number;
  pendingApproval: number;
  totalDisbursed: string;
  poolBalance: string;
  status: "active" | "paused";
}

const programs: Program[] = [
  { id: "dost-sei", name: "DOST-SEI Merit Scholarship", totalScholars: 47, pendingApproval: 12, totalDisbursed: "PHP 470,000", poolBalance: "PHP 530,000", status: "active" },
  { id: "ched-tulong", name: "CHED Tulong Dunong Program", totalScholars: 23, pendingApproval: 5, totalDisbursed: "PHP 280,000", poolBalance: "PHP 220,000", status: "active" },
];

export default function ManageProgramsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Manage Scholarships</h1>
        <p className="mt-1 text-[13px] text-gray-400">Approve scholars and disburse funds</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Total Scholars" value="70" icon={<Users className="h-4 w-4" />} />
        <StatCard label="Pending Approval" value="17" icon={<Clock className="h-4 w-4" />} highlight />
        <StatCard label="Total Disbursed" value="PHP 750K" icon={<Banknote className="h-4 w-4" />} />
        <StatCard label="Pool Balance" value="PHP 750K" icon={<Banknote className="h-4 w-4" />} />
      </div>

      {/* Programs */}
      <div className="space-y-3">
        {programs.map(program => (
          <Link key={program.id} href={`/programs/manage/${program.id}`} className="block rounded-xl border border-black/[0.04] bg-white p-4 transition-all hover:border-merit-gold/20 hover:shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-[14px] font-semibold text-gray-900">{program.name}</h3>
                <div className="flex items-center gap-4 mt-1.5 text-[11px] text-gray-400">
                  <span className="flex items-center gap-1"><Users className="h-3 w-3" />{program.totalScholars} scholars</span>
                  <span className="flex items-center gap-1"><Banknote className="h-3 w-3" />{program.totalDisbursed} disbursed</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {program.pendingApproval > 0 && (
                  <span className="flex items-center gap-1 rounded-md bg-amber-50 border border-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-700">
                    {program.pendingApproval} pending
                  </span>
                )}
                <ArrowUpRight className="h-4 w-4 text-gray-300" />
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value, icon, highlight }: { label: string; value: string; icon: React.ReactNode; highlight?: boolean }) {
  return (
    <div className="rounded-xl border border-black/[0.04] bg-white p-4">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-medium text-gray-400 uppercase tracking-wide">{label}</span>
        <span className="text-gray-300">{icon}</span>
      </div>
      <p className={`mt-1.5 text-[18px] font-semibold ${highlight ? "text-amber-600" : "text-gray-900"}`}>{value}</p>
    </div>
  );
}

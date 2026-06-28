"use client";

import { getUser } from "@/lib/auth";
import { ArrowUpRight, ArrowRight, TrendingUp, CheckCircle2, Clock, Banknote } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const user = getUser();
  const isAdmin = user?.role === "org_admin" || user?.role === "super_admin";

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">
          {isAdmin ? "Dashboard" : "Home"}
        </h1>
        <p className="mt-1 text-[13px] text-gray-400">
          {isAdmin ? "Manage programs and track disbursements" : "Track your applications and funding"}
        </p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
        <MetricCard
          label={isAdmin ? "Active Programs" : "Applications"}
          value="3"
          trend="+2"
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
        <MetricCard
          label={isAdmin ? "Total Recipients" : "Documents"}
          value="12"
          trend="+5"
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <MetricCard
          label={isAdmin ? "Disbursed" : "Received"}
          value="45,000"
          prefix="PHP"
          icon={<Banknote className="h-4 w-4" />}
          highlight
        />
        <MetricCard
          label={isAdmin ? "Compliance" : "Eligibility"}
          value={isAdmin ? "87%" : "Eligible"}
          trend={isAdmin ? "+4%" : undefined}
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
      </div>

      {/* Quick actions */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-[13px] font-medium text-gray-400 uppercase tracking-wider">Quick Actions</h2>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {isAdmin ? (
            <>
              <ActionCard title="Create Program" desc="Set up new funding criteria" href="/programs/new" />
              <ActionCard title="Review Queue" desc="3 documents awaiting review" href="/verifications" />
              <ActionCard title="Analytics" desc="View performance metrics" href="/analytics" />
            </>
          ) : (
            <>
              <ActionCard title="Explore Programs" desc="Browse available funding" href="/programs/browse" />
              <ActionCard title="Upload Document" desc="Submit for verification" href="/documents" />
              <ActionCard title="Wallet" desc="View balance and history" href="/wallet" />
            </>
          )}
        </div>
      </div>

      {/* Activity */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-[13px] font-medium text-gray-400 uppercase tracking-wider">Recent Activity</h2>
          <Link href="/notifications" className="text-[12px] font-medium text-merit-gold hover:text-gold-600 flex items-center gap-1">
            View all <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
        <div className="rounded-xl border border-black/[0.04] bg-white overflow-hidden">
          <ActivityRow icon={<CheckCircle2 className="h-4 w-4 text-emerald-500" />} text="Document verified successfully" time="2m ago" />
          <ActivityRow icon={<Banknote className="h-4 w-4 text-merit-gold" />} text="Funds disbursed — 500 XLM" time="1h ago" />
          <ActivityRow icon={<Clock className="h-4 w-4 text-merit-sky" />} text="Application submitted" time="3h ago" />
          <ActivityRow icon={<CheckCircle2 className="h-4 w-4 text-emerald-500" />} text="Eligibility confirmed" time="Yesterday" last />
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, trend, prefix, icon, highlight }: {
  label: string; value: string; trend?: string; prefix?: string; icon: React.ReactNode; highlight?: boolean;
}) {
  return (
    <div className="rounded-xl border border-black/[0.04] bg-white p-4">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">{label}</span>
        <span className="text-gray-300">{icon}</span>
      </div>
      <div className="mt-2">
        <span className={`text-[20px] font-semibold tracking-tight ${highlight ? "text-merit-gold" : "text-gray-900"}`}>
          {prefix && <span className="text-[13px] font-normal text-gray-400 mr-0.5">{prefix} </span>}
          {value}
        </span>
      </div>
      {trend && <span className="text-[11px] font-medium text-emerald-500 mt-1 inline-block">{trend}</span>}
    </div>
  );
}

function ActionCard({ title, desc, href }: { title: string; desc: string; href: string }) {
  return (
    <Link href={href} className="group flex items-center justify-between rounded-xl border border-black/[0.04] bg-white p-4 transition-all duration-150 hover:border-merit-gold/30 hover:shadow-sm">
      <div>
        <h3 className="text-[14px] font-medium text-gray-900">{title}</h3>
        <p className="mt-0.5 text-[12px] text-gray-400">{desc}</p>
      </div>
      <ArrowUpRight className="h-4 w-4 text-gray-300 transition-all group-hover:text-merit-gold group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
    </Link>
  );
}

function ActivityRow({ icon, text, time, last }: { icon: React.ReactNode; text: string; time: string; last?: boolean }) {
  return (
    <div className={`flex items-center gap-3 px-4 py-3 ${!last ? "border-b border-black/[0.03]" : ""}`}>
      {icon}
      <p className="flex-1 text-[13px] text-gray-700 truncate">{text}</p>
      <span className="text-[11px] text-gray-400 whitespace-nowrap">{time}</span>
    </div>
  );
}

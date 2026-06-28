"use client";

import { getUser } from "@/lib/auth";
import { ArrowUpRight, ArrowRight, TrendingUp, CheckCircle2, Clock, Banknote, FileText, Search, Upload, Wallet } from "lucide-react";
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
          {isAdmin ? "Manage programs and track disbursements" : "Track your scholarships and funding"}
        </p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
        <MetricCard label={isAdmin ? "Active Programs" : "Applications"} value={isAdmin ? "6" : "1"} trend="+1 new" icon={<FileText className="h-4 w-4" />} />
        <MetricCard label={isAdmin ? "Total Recipients" : "Documents"} value={isAdmin ? "47" : "3"} trend="verified" icon={<TrendingUp className="h-4 w-4" />} />
        <MetricCard label={isAdmin ? "Disbursed" : "Received"} value={isAdmin ? "PHP 450K" : "PHP 10K"} icon={<Banknote className="h-4 w-4" />} highlight />
        <MetricCard label={isAdmin ? "Compliance" : "Status"} value={isAdmin ? "87%" : "Eligible"} icon={<CheckCircle2 className="h-4 w-4" />} />
      </div>

      {/* Active scholarship for recipient */}
      {!isAdmin && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[13px] font-medium text-gray-400 uppercase tracking-wider">Active Scholarship</h2>
          </div>
          <div className="rounded-xl border border-emerald-100 bg-emerald-50/30 p-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-[14px] font-semibold text-gray-900">DOST-SEI Merit Scholarship</h3>
                <p className="text-[11px] text-gray-500 mt-0.5">Department of Science and Technology</p>
              </div>
              <span className="flex items-center gap-1 rounded-md bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
                <CheckCircle2 className="h-3 w-3" /> Verified
              </span>
            </div>
            <div className="mt-3 grid grid-cols-3 gap-3">
              <div>
                <p className="text-[10px] text-gray-400 uppercase tracking-wide">Amount</p>
                <p className="text-[13px] font-semibold text-gray-900">PHP 10,000</p>
              </div>
              <div>
                <p className="text-[10px] text-gray-400 uppercase tracking-wide">Status</p>
                <p className="text-[13px] font-semibold text-emerald-700">Disbursed</p>
              </div>
              <div>
                <p className="text-[10px] text-gray-400 uppercase tracking-wide">Next Review</p>
                <p className="text-[13px] font-semibold text-gray-900">Dec 2026</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick actions */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[13px] font-medium text-gray-400 uppercase tracking-wider">Quick Actions</h2>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {isAdmin ? (
            <>
              <ActionCard icon={<FileText className="h-4 w-4" />} title="Create Program" desc="Set up new funding criteria" href="/programs/new" />
              <ActionCard icon={<CheckCircle2 className="h-4 w-4" />} title="Review Queue" desc="3 documents pending" href="/verifications" />
              <ActionCard icon={<TrendingUp className="h-4 w-4" />} title="Analytics" desc="Performance metrics" href="/analytics" />
            </>
          ) : (
            <>
              <ActionCard icon={<Search className="h-4 w-4" />} title="Browse Scholarships" desc="6 programs available" href="/programs/browse" />
              <ActionCard icon={<Upload className="h-4 w-4" />} title="Upload Document" desc="Submit for verification" href="/documents" />
              <ActionCard icon={<Wallet className="h-4 w-4" />} title="My Wallet" desc="View balance" href="/wallet" />
            </>
          )}
        </div>
      </div>

      {/* Activity */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[13px] font-medium text-gray-400 uppercase tracking-wider">Recent Activity</h2>
          <Link href="/notifications" className="text-[12px] font-medium text-merit-gold hover:text-gold-600 flex items-center gap-1">
            View all <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
        <div className="rounded-xl border border-black/[0.04] bg-white overflow-hidden">
          <ActivityRow icon={<CheckCircle2 className="h-4 w-4 text-emerald-500" />} text="DOST-SEI scholarship verified and disbursed" time="2d ago" />
          <ActivityRow icon={<FileText className="h-4 w-4 text-merit-gold" />} text="Grade slip uploaded and processed" time="3d ago" />
          <ActivityRow icon={<Clock className="h-4 w-4 text-sky-400" />} text="Application submitted to DOST-SEI" time="1w ago" />
          <ActivityRow icon={<CheckCircle2 className="h-4 w-4 text-emerald-500" />} text="Wallet connected to Stellar testnet" time="1w ago" last />
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, trend, icon, highlight }: { label: string; value: string; trend?: string; icon: React.ReactNode; highlight?: boolean }) {
  return (
    <div className="rounded-xl border border-black/[0.04] bg-white p-4">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">{label}</span>
        <span className="text-gray-300">{icon}</span>
      </div>
      <p className={`mt-2 text-[20px] font-semibold tracking-tight ${highlight ? "text-merit-gold" : "text-gray-900"}`}>{value}</p>
      {trend && <span className="text-[11px] font-medium text-emerald-500 mt-0.5 inline-block">{trend}</span>}
    </div>
  );
}

function ActionCard({ icon, title, desc, href }: { icon: React.ReactNode; title: string; desc: string; href: string }) {
  return (
    <Link href={href} className="group flex items-center justify-between rounded-xl border border-black/[0.04] bg-white p-4 transition-all duration-150 hover:border-merit-gold/30 hover:shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#FAFAF9] text-gray-400 group-hover:text-merit-gold transition-colors">{icon}</div>
        <div>
          <h3 className="text-[13px] font-medium text-gray-900">{title}</h3>
          <p className="text-[11px] text-gray-400">{desc}</p>
        </div>
      </div>
      <ArrowUpRight className="h-4 w-4 text-gray-300 transition-all group-hover:text-merit-gold" />
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

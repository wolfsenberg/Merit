"use client";

import { getUser } from "@/lib/auth";
import { Card, CardContent } from "@/components/ui/card";

export default function DashboardPage() {
  const user = getUser();
  const isAdmin = user?.role === "org_admin" || user?.role === "super_admin";

  return (
    <div className="space-y-6">
      {/* Welcome banner */}
      <div className="rounded-2xl bg-gradient-to-r from-[#F4BA45] to-[#E5A830] p-5 md:p-6 text-white shadow-lg shadow-[#F4BA45]/20">
        <h1 className="text-lg font-bold md:text-xl">
          Welcome back{user?.full_name ? `, ${user.full_name}` : ""} 👋
        </h1>
        <p className="mt-1 text-white/80 text-sm">
          {isAdmin ? "Manage your programs and track disbursements" : "Track your applications and funding status"}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label={isAdmin ? "Active Programs" : "Applications"} value="3" change="+2 this month" />
        <StatCard label={isAdmin ? "Recipients" : "Documents"} value="12" change="+5 this week" />
        <StatCard label={isAdmin ? "Total Funded" : "Received"} value="₱45K" change="on Stellar" accent />
        <StatCard label={isAdmin ? "Compliance" : "Status"} value={isAdmin ? "87%" : "Eligible"} change={isAdmin ? "↑ 4%" : "✓ Verified"} />
      </div>

      {/* Quick actions */}
      <div className="space-y-3">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {isAdmin ? (
            <>
              <ActionCard emoji="📋" title="Create Program" desc="Set up a new funding program" href="/programs/new" />
              <ActionCard emoji="📄" title="Review Documents" desc="3 documents pending review" href="/verifications" />
              <ActionCard emoji="📊" title="View Analytics" desc="Program performance metrics" href="/analytics" />
            </>
          ) : (
            <>
              <ActionCard emoji="🔍" title="Browse Programs" desc="Find programs to apply to" href="/programs/browse" />
              <ActionCard emoji="📤" title="Upload Document" desc="Submit compliance documents" href="/documents" />
              <ActionCard emoji="💰" title="My Wallet" desc="View balance & transactions" href="/wallet" />
            </>
          )}
        </div>
      </div>

      {/* Activity */}
      <div className="space-y-3">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Recent Activity</h2>
        <Card className="rounded-2xl border-merit-peach/50 shadow-sm">
          <CardContent className="divide-y divide-merit-peach/30 p-0">
            <ActivityItem icon="✅" text="Document verified successfully" time="2 min ago" />
            <ActivityItem icon="💸" text="Funds disbursed — 500 XLM" time="1 hour ago" />
            <ActivityItem icon="📝" text="New application submitted" time="3 hours ago" />
            <ActivityItem icon="🔔" text="Eligibility status updated" time="Yesterday" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatCard({ label, value, change, accent }: { label: string; value: string; change: string; accent?: boolean }) {
  return (
    <Card className="rounded-xl border-merit-peach/40 shadow-sm">
      <CardContent className="p-4">
        <p className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">{label}</p>
        <p className={`mt-1 text-xl font-bold ${accent ? "text-merit-gold" : "text-gray-900"}`}>{value}</p>
        <p className="text-[11px] text-emerald-600 font-medium mt-0.5">{change}</p>
      </CardContent>
    </Card>
  );
}

function ActionCard({ emoji, title, desc, href }: { emoji: string; title: string; desc: string; href: string }) {
  return (
    <a href={href} className="group block rounded-xl border border-merit-peach/50 bg-white p-4 shadow-sm transition-all hover:shadow-md hover:border-merit-gold/40 hover:-translate-y-0.5 active:translate-y-0">
      <span className="text-2xl">{emoji}</span>
      <h3 className="mt-2 text-sm font-semibold text-gray-900 group-hover:text-gold-700">{title}</h3>
      <p className="mt-0.5 text-xs text-gray-500">{desc}</p>
    </a>
  );
}

function ActivityItem({ icon, text, time }: { icon: string; text: string; time: string }) {
  return (
    <div className="flex items-center gap-3 px-4 py-3">
      <span className="text-base">{icon}</span>
      <p className="flex-1 text-sm text-gray-700 truncate">{text}</p>
      <span className="text-[11px] text-gray-400 whitespace-nowrap">{time}</span>
    </div>
  );
}

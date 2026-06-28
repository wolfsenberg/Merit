"use client";

import { getUser } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DashboardPage() {
  const user = getUser();
  const isAdmin = user?.role === "org_admin" || user?.role === "super_admin";

  return (
    <div className="space-y-6">
      {/* Welcome header */}
      <div className="rounded-2xl bg-gradient-to-r from-amber-500 to-amber-600 p-6 text-white shadow-lg shadow-amber-500/20">
        <h1 className="text-xl font-bold md:text-2xl">
          Welcome back{user?.full_name ? `, ${user.full_name}` : ""} 👋
        </h1>
        <p className="mt-1 text-amber-100 text-sm">
          {isAdmin ? "Manage your programs and track disbursements" : "Track your applications and funding status"}
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
        <Card className="rounded-xl border-0 shadow-sm">
          <CardContent className="p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              {isAdmin ? "Active Programs" : "Applications"}
            </p>
            <p className="mt-1 text-2xl font-bold text-gray-900">3</p>
            <p className="text-xs text-emerald-600 font-medium mt-1">+2 this month</p>
          </CardContent>
        </Card>
        <Card className="rounded-xl border-0 shadow-sm">
          <CardContent className="p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              {isAdmin ? "Recipients" : "Documents"}
            </p>
            <p className="mt-1 text-2xl font-bold text-gray-900">12</p>
            <p className="text-xs text-emerald-600 font-medium mt-1">+5 this week</p>
          </CardContent>
        </Card>
        <Card className="rounded-xl border-0 shadow-sm">
          <CardContent className="p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              {isAdmin ? "Total Funded" : "Received"}
            </p>
            <p className="mt-1 text-2xl font-bold text-gray-900">₱45K</p>
            <p className="text-xs text-amber-600 font-medium mt-1">on Stellar</p>
          </CardContent>
        </Card>
        <Card className="rounded-xl border-0 shadow-sm">
          <CardContent className="p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              {isAdmin ? "Compliance Rate" : "Status"}
            </p>
            <p className="mt-1 text-2xl font-bold text-gray-900">{isAdmin ? "87%" : "Eligible"}</p>
            <p className="text-xs text-emerald-600 font-medium mt-1">{isAdmin ? "↑ 4%" : "✓ Verified"}</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick actions */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
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

      {/* Recent activity */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Recent Activity</h2>
        <Card className="rounded-xl border-0 shadow-sm">
          <CardContent className="divide-y p-0">
            <ActivityItem icon="✅" text="Document verified successfully" time="2 min ago" />
            <ActivityItem icon="💸" text="Funds disbursed — 500 XLM" time="1 hour ago" />
            <ActivityItem icon="📝" text="New application submitted" time="3 hours ago" />
            <ActivityItem icon="🔔" text="Eligibility status: Eligible" time="Yesterday" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function ActionCard({ emoji, title, desc, href }: { emoji: string; title: string; desc: string; href: string }) {
  return (
    <a href={href} className="group block rounded-xl border border-gray-100 bg-white p-4 shadow-sm transition-all hover:shadow-md hover:border-amber-200 hover:-translate-y-0.5">
      <span className="text-2xl">{emoji}</span>
      <h3 className="mt-2 text-sm font-semibold text-gray-900 group-hover:text-amber-700">{title}</h3>
      <p className="mt-0.5 text-xs text-gray-500">{desc}</p>
    </a>
  );
}

function ActivityItem({ icon, text, time }: { icon: string; text: string; time: string }) {
  return (
    <div className="flex items-center gap-3 px-4 py-3">
      <span className="text-base">{icon}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-700 truncate">{text}</p>
      </div>
      <span className="text-xs text-gray-400 whitespace-nowrap">{time}</span>
    </div>
  );
}

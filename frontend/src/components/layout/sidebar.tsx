"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { getUser } from "@/lib/auth";
import { cn } from "@/lib/utils";
import {
  LayoutGrid, FileText, ShieldCheck, BarChart3, Bell,
  Search, Wallet, Users, Building2, ScrollText, Zap, Receipt, PiggyBank,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface NavItem { label: string; href: string; icon: LucideIcon; }

const orgAdminNav: NavItem[] = [
  { label: "Overview", href: "/dashboard", icon: LayoutGrid },
  { label: "Programs", href: "/programs", icon: FileText },
  { label: "Verifications", href: "/verifications", icon: ShieldCheck },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Notifications", href: "/notifications", icon: Bell },
];

const recipientNav: NavItem[] = [
  { label: "Home", href: "/dashboard", icon: LayoutGrid },
  { label: "Scholars Hub", href: "/programs/browse", icon: Search },
  { label: "Transactions", href: "/transactions", icon: Receipt },
  { label: "Savings", href: "/savings", icon: PiggyBank },
  { label: "Wallet", href: "/wallet", icon: Wallet },
  { label: "Alerts", href: "/notifications", icon: Bell },
];

const adminNav: NavItem[] = [
  { label: "Overview", href: "/admin/dashboard", icon: Zap },
  { label: "Users", href: "/admin/users", icon: Users },
  { label: "Organizations", href: "/admin/organizations", icon: Building2 },
  { label: "Audit Trail", href: "/admin/audit-logs", icon: ScrollText },
  { label: "Notifications", href: "/notifications", icon: Bell },
];

export function getNavItems(role?: string): NavItem[] {
  switch (role) { case "super_admin": return adminNav; case "org_admin": return orgAdminNav; default: return recipientNav; }
}

interface SidebarProps { isOpen: boolean; onClose: () => void; }

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const user = getUser();
  const navItems = getNavItems(user?.role);

  return (
    <>
      {isOpen && <div className="fixed inset-0 z-40 bg-black/10 backdrop-blur-[2px] md:hidden" onClick={onClose} />}

      <aside className={cn(
        "fixed inset-y-0 left-0 z-50 flex w-[260px] flex-col bg-white/95 backdrop-blur-xl border-r border-black/[0.04] transition-transform duration-200 ease-out md:static md:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        {/* Logo */}
        <div className="flex h-[60px] items-center px-6">
          <Link href="/dashboard" className="flex items-center gap-3" onClick={onClose}>
            <img src="/logo.svg" alt="Merit" className="h-8 w-8" />
            <span className="text-[17px] font-semibold tracking-tight text-gray-900">Merit</span>
          </Link>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-3 pt-2">
          <ul className="space-y-0.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
              return (
                <li key={item.href}>
                  <Link href={item.href} onClick={onClose}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-150",
                      isActive
                        ? "bg-merit-gold/10 text-gray-900"
                        : "text-gray-500 hover:bg-black/[0.03] hover:text-gray-900"
                    )}>
                    <Icon className={cn("h-[18px] w-[18px]", isActive ? "text-merit-gold" : "text-gray-400")} strokeWidth={1.8} />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer */}
        <div className="border-t border-black/[0.04] p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-merit-gold to-[#E5A830] text-[11px] font-semibold text-white">
              {user?.full_name?.charAt(0)?.toUpperCase() || "U"}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[12px] font-medium text-gray-900 truncate">{user?.full_name || "User"}</p>
              <p className="text-[11px] text-gray-400 capitalize">{user?.role?.replace("_", " ") || "recipient"}</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

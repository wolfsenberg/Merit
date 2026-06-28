"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { getUser } from "@/lib/auth";
import { cn } from "@/lib/utils";

export interface NavItem {
  label: string;
  href: string;
  icon: string;
}

const orgAdminNav: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: "📊" },
  { label: "Programs", href: "/programs", icon: "📋" },
  { label: "Verifications", href: "/verifications", icon: "✅" },
  { label: "Analytics", href: "/analytics", icon: "📈" },
  { label: "Notifications", href: "/notifications", icon: "🔔" },
];

const recipientNav: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: "🏠" },
  { label: "Programs", href: "/programs/browse", icon: "🔍" },
  { label: "Documents", href: "/documents", icon: "📄" },
  { label: "Wallet", href: "/wallet", icon: "💰" },
  { label: "Notifications", href: "/notifications", icon: "🔔" },
];

const adminNav: NavItem[] = [
  { label: "Dashboard", href: "/admin/dashboard", icon: "⚡" },
  { label: "Users", href: "/admin/users", icon: "👥" },
  { label: "Organizations", href: "/admin/organizations", icon: "🏢" },
  { label: "Audit Logs", href: "/admin/audit-logs", icon: "🛡️" },
  { label: "Notifications", href: "/notifications", icon: "🔔" },
];

export function getNavItems(role?: string): NavItem[] {
  switch (role) {
    case "super_admin": return adminNav;
    case "org_admin": return orgAdminNav;
    default: return recipientNav;
  }
}

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const user = getUser();
  const navItems = getNavItems(user?.role);

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm md:hidden" onClick={onClose} />
      )}

      {/* Sidebar */}
      <aside className={cn(
        "fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-white border-r border-gray-100 transition-transform duration-200 ease-out md:static md:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        {/* Logo */}
        <div className="flex h-14 items-center px-5 border-b border-gray-100">
          <Link href="/dashboard" className="flex items-center gap-2.5" onClick={onClose}>
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 shadow-sm shadow-amber-500/20">
              <span className="text-sm font-bold text-white">M</span>
            </div>
            <span className="text-lg font-bold text-gray-900">Merit</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <ul className="space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={onClose}
                    className={cn(
                      "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all",
                      isActive
                        ? "bg-amber-50 text-amber-700 shadow-sm"
                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    )}
                  >
                    <span className="text-base">{item.icon}</span>
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* User role badge */}
        <div className="border-t border-gray-100 p-4">
          <div className="flex items-center gap-2 rounded-xl bg-gray-50 px-3 py-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-amber-100 text-xs font-semibold text-amber-700">
              {user?.full_name?.charAt(0)?.toUpperCase() || "U"}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-gray-900 truncate">{user?.full_name || "User"}</p>
              <p className="text-[10px] text-gray-500 capitalize">{user?.role?.replace("_", " ") || "recipient"}</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

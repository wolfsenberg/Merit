"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  Users,
  Wallet,
  Bell,
  Shield,
  ClipboardCheck,
  Building2,
  Upload,
  BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const orgAdminNav: NavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: <LayoutDashboard className="h-5 w-5" />,
  },
  {
    label: "Programs",
    href: "/programs",
    icon: <FileText className="h-5 w-5" />,
  },
  {
    label: "Verifications",
    href: "/verifications",
    icon: <ClipboardCheck className="h-5 w-5" />,
  },
  {
    label: "Analytics",
    href: "/analytics",
    icon: <BarChart3 className="h-5 w-5" />,
  },
  {
    label: "Notifications",
    href: "/notifications",
    icon: <Bell className="h-5 w-5" />,
  },
];

const recipientNav: NavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: <LayoutDashboard className="h-5 w-5" />,
  },
  {
    label: "Programs",
    href: "/programs",
    icon: <FileText className="h-5 w-5" />,
  },
  {
    label: "Documents",
    href: "/documents",
    icon: <Upload className="h-5 w-5" />,
  },
  {
    label: "Wallet",
    href: "/wallet",
    icon: <Wallet className="h-5 w-5" />,
  },
  {
    label: "Notifications",
    href: "/notifications",
    icon: <Bell className="h-5 w-5" />,
  },
];

const adminNav: NavItem[] = [
  {
    label: "Dashboard",
    href: "/admin/dashboard",
    icon: <LayoutDashboard className="h-5 w-5" />,
  },
  {
    label: "Users",
    href: "/admin/users",
    icon: <Users className="h-5 w-5" />,
  },
  {
    label: "Organizations",
    href: "/admin/organizations",
    icon: <Building2 className="h-5 w-5" />,
  },
  {
    label: "Audit Logs",
    href: "/admin/audit-logs",
    icon: <Shield className="h-5 w-5" />,
  },
  {
    label: "Notifications",
    href: "/notifications",
    icon: <Bell className="h-5 w-5" />,
  },
];

/** Returns navigation items based on user role */
export function getNavItems(role?: string): NavItem[] {
  switch (role) {
    case "super_admin":
      return adminNav;
    case "org_admin":
      return orgAdminNav;
    case "recipient":
      return recipientNav;
    default:
      return recipientNav;
  }
}

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  // For now, use default nav until auth context is wired up
  const navItems = getNavItems();

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-border bg-white transition-transform duration-300 ease-in-out md:static md:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
        role="navigation"
        aria-label="Main navigation"
      >
        {/* Logo area */}
        <div className="flex h-16 items-center border-b border-border px-6">
          <Link href="/dashboard" className="flex items-center gap-2" onClick={onClose}>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gold-500">
              <span className="text-sm font-bold text-white">M</span>
            </div>
            <span className="text-xl font-bold text-foreground">Merit</span>
          </Link>
        </div>

        {/* Navigation links */}
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
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-gold-50 text-gold-700"
                        : "text-muted-foreground hover:bg-gold-50/50 hover:text-foreground"
                    )}
                    aria-current={isActive ? "page" : undefined}
                  >
                    <span className={cn(isActive ? "text-gold-600" : "text-muted-foreground")}>
                      {item.icon}
                    </span>
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer area */}
        <div className="border-t border-border p-4">
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} Merit Platform
          </p>
        </div>
      </aside>
    </>
  );
}

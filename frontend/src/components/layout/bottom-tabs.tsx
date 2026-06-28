"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutGrid, Search, PiggyBank, Receipt, Wallet } from "lucide-react";
import { cn } from "@/lib/utils";

interface TabItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const tabs: TabItem[] = [
  { label: "Home", href: "/dashboard", icon: <LayoutGrid className="h-5 w-5" strokeWidth={1.5} /> },
  { label: "Feed", href: "/programs/browse", icon: <Search className="h-5 w-5" strokeWidth={1.5} /> },
  { label: "Savings", href: "/savings", icon: <PiggyBank className="h-5 w-5" strokeWidth={1.5} /> },
  { label: "History", href: "/transactions", icon: <Receipt className="h-5 w-5" strokeWidth={1.5} /> },
  { label: "Wallet", href: "/wallet", icon: <Wallet className="h-5 w-5" strokeWidth={1.5} /> },
];

export function BottomTabs() {
  const pathname = usePathname();

  return (
    <nav className="flex items-center justify-around border-t border-black/[0.06] bg-white px-2 py-2.5 shrink-0">
      {tabs.map((tab) => {
        const isActive = pathname === tab.href || pathname.startsWith(tab.href + "/");
        return (
          <Link key={tab.href} href={tab.href} className={cn("flex flex-col items-center gap-0.5 px-3 py-1 transition-colors", isActive ? "text-merit-gold" : "text-gray-400")}>
            {tab.icon}
            <span className="text-[9px] font-medium">{tab.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { clearTokens, getUser } from "@/lib/auth";

interface HeaderProps {
  onMenuToggle: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  const router = useRouter();
  const user = getUser();

  const handleLogout = () => {
    clearTokens();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center border-b border-gray-100 bg-white/80 backdrop-blur-md px-4 md:px-6">
      {/* Mobile menu toggle */}
      <button
        className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-600 hover:bg-gray-100 md:hidden"
        onClick={onMenuToggle}
        aria-label="Toggle menu"
      >
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Mobile logo */}
      <Link href="/dashboard" className="flex items-center gap-2 md:hidden ml-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-amber-500 to-amber-600">
          <span className="text-xs font-bold text-white">M</span>
        </div>
        <span className="text-base font-bold text-gray-900">Merit</span>
      </Link>

      <div className="flex-1" />

      {/* User area */}
      <div className="flex items-center gap-2">
        {user && (
          <span className="hidden md:block text-sm text-gray-600">
            {user.full_name || user.email}
          </span>
        )}
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-100 text-xs font-semibold text-amber-700">
          {user?.full_name?.charAt(0)?.toUpperCase() || "U"}
        </div>
        <button
          onClick={handleLogout}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          aria-label="Logout"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </div>
    </header>
  );
}

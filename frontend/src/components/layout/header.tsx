"use client";

import Link from "next/link";
import { Menu, LogOut, User } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  onMenuToggle: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center border-b border-border bg-white px-4 md:px-6">
      {/* Mobile menu toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        onClick={onMenuToggle}
        aria-label="Toggle navigation menu"
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Logo - visible on mobile only (desktop has sidebar logo) */}
      <Link href="/dashboard" className="flex items-center gap-2 md:hidden ml-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gold-500">
          <span className="text-xs font-bold text-white">M</span>
        </div>
        <span className="text-lg font-bold text-foreground">Merit</span>
      </Link>

      {/* Spacer */}
      <div className="flex-1" />

      {/* User profile area */}
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/profile" aria-label="User profile">
            <User className="h-5 w-5" />
          </Link>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Logout"
          onClick={() => {
            // Logout will be handled by auth context in task 13.2
          }}
        >
          <LogOut className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
}

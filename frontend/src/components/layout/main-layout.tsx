"use client";

import { useState } from "react";
import { Sidebar } from "./sidebar";
import { Header } from "./header";
import { BottomTabs } from "./bottom-tabs";
import { useMobilePreview } from "./mobile-preview";

export function MainLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { isMobilePreview } = useMobilePreview();

  if (isMobilePreview) {
    // Mobile preview: no sidebar, bottom tabs pinned inside container
    return (
      <div className="flex flex-col h-full bg-[#FAFAF9]">
        <Header onMenuToggle={() => {}} />
        <main className="flex-1 overflow-y-auto">
          <div className="px-4 py-5">
            {children}
          </div>
        </main>
        <BottomTabs />
      </div>
    );
  }

  // Desktop: full layout with sidebar
  return (
    <div className="flex h-screen overflow-hidden bg-[#FAFAF9]">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header onMenuToggle={() => setSidebarOpen(p => !p)} />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-[1100px] px-4 py-6 md:px-8 md:py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

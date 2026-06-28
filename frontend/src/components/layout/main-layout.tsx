"use client";

import { useState } from "react";
import { Sidebar } from "./sidebar";
import { Header } from "./header";
import { BottomTabs } from "./bottom-tabs";
import { useMobilePreview } from "./mobile-preview";

export function MainLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { isMobilePreview } = useMobilePreview();

  return (
    <div className="flex h-full min-h-screen overflow-hidden bg-[#FAFAF9]">
      {/* Sidebar only on desktop view */}
      {!isMobilePreview && <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header onMenuToggle={() => setSidebarOpen(p => !p)} />
        <main className="flex-1 overflow-y-auto pb-16">
          <div className={`mx-auto px-4 py-5 ${isMobilePreview ? "" : "md:max-w-[1100px] md:px-8 md:py-8"}`}>
            {children}
          </div>
        </main>
        {/* Bottom tabs — always in mobile preview, only on small screens in desktop mode */}
        <BottomTabs />
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import { Smartphone, X, Monitor } from "lucide-react";

interface MobilePreviewProps {
  children: React.ReactNode;
}

export function MobilePreviewWrapper({ children }: MobilePreviewProps) {
  const [mobileView, setMobileView] = useState(false);

  return (
    <>
      {/* Toggle button — only visible on desktop */}
      <button
        onClick={() => setMobileView(!mobileView)}
        className="fixed bottom-5 right-5 z-[100] hidden md:flex h-10 w-10 items-center justify-center rounded-full bg-gray-900 text-white shadow-lg hover:bg-gray-800 transition-all hover:scale-105"
        aria-label={mobileView ? "Exit mobile preview" : "Mobile preview"}
        title={mobileView ? "Back to desktop" : "Preview mobile view"}
      >
        {mobileView ? <Monitor className="h-4 w-4" /> : <Smartphone className="h-4 w-4" />}
      </button>

      {/* Render */}
      {mobileView ? (
        <div className="hidden md:flex h-screen items-center justify-center bg-gray-100 p-8">
          {/* Phone frame */}
          <div className="relative">
            {/* Phone shell */}
            <div className="relative w-[375px] h-[812px] rounded-[3rem] border-[12px] border-gray-900 bg-gray-900 shadow-2xl overflow-hidden">
              {/* Notch */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[120px] h-[28px] bg-gray-900 rounded-b-2xl z-10" />
              {/* Screen */}
              <div className="w-full h-full rounded-[2.2rem] overflow-hidden bg-white">
                <div className="w-full h-full overflow-y-auto">
                  {children}
                </div>
              </div>
              {/* Home indicator */}
              <div className="absolute bottom-2 left-1/2 -translate-x-1/2 w-[120px] h-[4px] rounded-full bg-white/30" />
            </div>
            {/* Label */}
            <p className="text-center mt-4 text-[12px] text-gray-500">iPhone 14 Pro — 375 × 812</p>
          </div>
        </div>
      ) : (
        children
      )}
    </>
  );
}

"use client";

import { useState, createContext, useContext } from "react";
import { Monitor, Smartphone } from "lucide-react";

interface MobilePreviewContextType {
  isMobilePreview: boolean;
  toggle: () => void;
}

const MobilePreviewContext = createContext<MobilePreviewContextType>({ isMobilePreview: false, toggle: () => {} });

export function useMobilePreview() {
  return useContext(MobilePreviewContext);
}

export function MobilePreviewWrapper({ children }: { children: React.ReactNode }) {
  const [isMobilePreview, setIsMobilePreview] = useState(true);

  const toggle = () => setIsMobilePreview(prev => !prev);

  return (
    <MobilePreviewContext.Provider value={{ isMobilePreview, toggle }}>
      {/* Toggle button — fixed bottom right, always outside container */}
      <button
        onClick={toggle}
        className="fixed bottom-6 right-6 z-[9999] hidden md:flex items-center gap-2 rounded-full bg-gray-900 px-4 py-2.5 text-[12px] font-medium text-white shadow-xl hover:bg-gray-800 transition-all hover:scale-105"
      >
        {isMobilePreview ? (
          <><Monitor className="h-3.5 w-3.5" /> Desktop View</>
        ) : (
          <><Smartphone className="h-3.5 w-3.5" /> Mobile View</>
        )}
      </button>

      {isMobilePreview ? (
        /* Mobile view on desktop: fixed phone-sized container centered */
        <div className="hidden md:flex h-screen w-screen items-center justify-center bg-[#E5E5E5]">
          <div className="relative w-[420px] h-[780px] bg-white shadow-2xl overflow-hidden flex flex-col">
            {children}
          </div>
        </div>
      ) : (
        /* Desktop: full width, normal behavior */
        children
      )}

      {/* Actual mobile: just render normally, no wrapper */}
      <div className="contents md:hidden">
      </div>
    </MobilePreviewContext.Provider>
  );
}

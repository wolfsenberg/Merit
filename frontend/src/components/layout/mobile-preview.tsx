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
      {/* Floating toggle — bottom right, outside the mobile container */}
      <button
        onClick={toggle}
        className="fixed bottom-6 right-6 z-[200] hidden md:flex items-center gap-2 rounded-full bg-gray-900 px-4 py-2.5 text-[12px] font-medium text-white shadow-xl hover:bg-gray-800 transition-all hover:scale-105"
      >
        {isMobilePreview ? (
          <><Monitor className="h-3.5 w-3.5" /> Desktop View</>
        ) : (
          <><Smartphone className="h-3.5 w-3.5" /> Mobile View</>
        )}
      </button>

      {/* Content */}
      {isMobilePreview ? (
        <div className="hidden md:flex min-h-screen items-start justify-center bg-[#E8E8E8] pt-6 pb-6">
          <div className="w-[390px] min-h-[780px] max-h-[90vh] overflow-y-auto bg-white shadow-2xl relative">
            {children}
          </div>
        </div>
      ) : (
        children
      )}

      {/* On actual mobile screens, always render children directly */}
      <div className="md:hidden">
      </div>
    </MobilePreviewContext.Provider>
  );
}

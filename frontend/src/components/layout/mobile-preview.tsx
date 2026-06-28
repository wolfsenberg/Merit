"use client";

import { useState, createContext, useContext } from "react";

interface MobilePreviewContextType {
  isMobilePreview: boolean;
  toggle: () => void;
}

const MobilePreviewContext = createContext<MobilePreviewContextType>({ isMobilePreview: false, toggle: () => {} });

export function useMobilePreview() {
  return useContext(MobilePreviewContext);
}

export function MobilePreviewWrapper({ children }: { children: React.ReactNode }) {
  const [isMobilePreview, setIsMobilePreview] = useState(false);

  const toggle = () => setIsMobilePreview(prev => !prev);

  return (
    <MobilePreviewContext.Provider value={{ isMobilePreview, toggle }}>
      {isMobilePreview ? (
        <div className="hidden md:flex h-screen items-center justify-center bg-[#E8E8E8]">
          <div className="w-[390px] h-screen max-h-[844px] overflow-hidden rounded-2xl shadow-2xl border border-black/10 bg-white">
            <div className="w-full h-full overflow-y-auto">
              {children}
            </div>
          </div>
        </div>
      ) : (
        children
      )}
    </MobilePreviewContext.Provider>
  );
}

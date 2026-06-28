"use client";

import { useState, createContext, useContext, useEffect } from "react";
import { Monitor, Smartphone, Languages } from "lucide-react";

interface MobilePreviewContextType {
  isMobilePreview: boolean;
  toggle: () => void;
}

const MobilePreviewContext = createContext<MobilePreviewContextType>({ isMobilePreview: false, toggle: () => {} });

export function useMobilePreview() {
  return useContext(MobilePreviewContext);
}

function getStoredView(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem("merit_view_mode") === "mobile";
}

export function MobilePreviewWrapper({ children }: { children: React.ReactNode }) {
  const [isMobilePreview, setIsMobilePreview] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setIsMobilePreview(getStoredView());
    setMounted(true);
  }, []);

  const toggle = () => {
    const next = !isMobilePreview;
    setIsMobilePreview(next);
    localStorage.setItem("merit_view_mode", next ? "mobile" : "desktop");
  };

  if (!mounted) return <>{children}</>;

  return (
    <MobilePreviewContext.Provider value={{ isMobilePreview, toggle }}>
      {/* Floating controls — bottom right */}
      <div className="fixed bottom-6 right-6 z-[9999] hidden md:flex flex-col gap-2 items-end">
        <button
          onClick={toggle}
          className="flex items-center gap-2 rounded-full bg-gray-900 px-4 py-2.5 text-[12px] font-medium text-white shadow-xl hover:bg-gray-800 transition-all hover:scale-105"
        >
          {isMobilePreview ? (
            <><Monitor className="h-3.5 w-3.5" /> Desktop View</>
          ) : (
            <><Smartphone className="h-3.5 w-3.5" /> Mobile View</>
          )}
        </button>
        <LangToggleButton />
      </div>

      {isMobilePreview ? (
        <div className="hidden md:flex h-screen w-screen items-center justify-center bg-[#E5E5E5]">
          <div className="relative w-[420px] h-[780px] bg-white shadow-2xl overflow-hidden flex flex-col">
            {children}
          </div>
        </div>
      ) : (
        children
      )}
    </MobilePreviewContext.Provider>
  );
}

// Self-contained lang toggle that reads/writes localStorage directly
// (doesn't depend on LangProvider context order)
function LangToggleButton() {
  const [lang, setLang] = useState<"en" | "tl">("en");

  useEffect(() => {
    const stored = localStorage.getItem("merit_lang");
    if (stored === "tl") setLang("tl");
  }, []);

  const handleToggle = () => {
    const next = lang === "en" ? "tl" : "en";
    setLang(next);
    localStorage.setItem("merit_lang", next);
    // Force re-render across app
    window.dispatchEvent(new Event("merit-lang-change"));
    window.location.reload();
  };

  return (
    <button
      onClick={handleToggle}
      className="flex items-center gap-2 rounded-full bg-merit-gold px-4 py-2.5 text-[12px] font-medium text-white shadow-xl hover:bg-gold-500 transition-all hover:scale-105"
    >
      <Languages className="h-3.5 w-3.5" />
      {lang === "en" ? "Taglish" : "English"}
    </button>
  );
}

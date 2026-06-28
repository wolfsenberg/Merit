"use client";

import { useState, createContext, useContext, useEffect, useRef } from "react";
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
        <LangDropdown />
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

function LangDropdown() {
  const [lang, setLang] = useState<"en" | "tl">("en");
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stored = localStorage.getItem("merit_lang");
    if (stored === "tl") setLang("tl");
  }, []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (selected: "en" | "tl") => {
    setLang(selected);
    localStorage.setItem("merit_lang", selected);
    setOpen(false);
    window.location.reload();
  };

  const label = lang === "en" ? "English" : "Tagalog";

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-full bg-merit-gold px-4 py-2.5 text-[12px] font-medium text-white shadow-xl hover:bg-gold-500 transition-all hover:scale-105"
      >
        <Languages className="h-3.5 w-3.5" />
        Language: {label}
      </button>

      {open && (
        <div className="absolute bottom-full mb-2 right-0 w-[160px] rounded-xl bg-white border border-black/[0.06] shadow-xl overflow-hidden animate-in">
          <button
            onClick={() => handleSelect("en")}
            className={`w-full text-left px-4 py-3 text-[13px] font-medium transition-colors ${lang === "en" ? "bg-merit-gold/10 text-merit-gold" : "text-gray-700 hover:bg-gray-50"}`}
          >
            English
          </button>
          <button
            onClick={() => handleSelect("tl")}
            className={`w-full text-left px-4 py-3 text-[13px] font-medium border-t border-black/[0.04] transition-colors ${lang === "tl" ? "bg-merit-gold/10 text-merit-gold" : "text-gray-700 hover:bg-gray-50"}`}
          >
            Tagalog
          </button>
        </div>
      )}
    </div>
  );
}

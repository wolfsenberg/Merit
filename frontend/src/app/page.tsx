"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { isAuthenticated } from "@/lib/auth";

export default function HomePage() {
  const router = useRouter();
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    // Show the splash screen briefly
    setShowContent(true);

    const timer = setTimeout(() => {
      if (isAuthenticated()) {
        router.replace("/dashboard");
      } else {
        router.replace("/login");
      }
    }, 2000); // Show splash for 2 seconds

    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className="flex h-screen flex-col items-center justify-center bg-merit-cream">
      {/* Background decoration */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-32 -right-32 h-64 w-64 rounded-full bg-merit-peach/50 blur-3xl" />
        <div className="absolute -bottom-32 -left-32 h-64 w-64 rounded-full bg-merit-sky/15 blur-3xl" />
      </div>

      {/* Splash content */}
      <div className={`relative flex flex-col items-center gap-5 transition-all duration-700 ${showContent ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}>
        {/* Logo */}
        <div className="relative">
          <Image
            src="/logo.svg"
            alt="Merit Logo"
            width={88}
            height={88}
            className="drop-shadow-lg"
            priority
          />
        </div>

        {/* Brand name */}
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Merit</h1>
          <p className="mt-2 text-sm text-gray-500 italic">Your merit, your future.</p>
        </div>

        {/* Loading indicator */}
        <div className="mt-4 flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-merit-sky animate-bounce [animation-delay:0ms]" />
          <div className="h-2 w-2 rounded-full bg-merit-sky animate-bounce [animation-delay:150ms]" />
          <div className="h-2 w-2 rounded-full bg-merit-sky animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}

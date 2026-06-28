"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated()) {
      router.replace("/dashboard");
    } else {
      // Check if user has seen onboarding
      const seen = localStorage.getItem("merit_onboarding_seen");
      if (seen) {
        router.replace("/login");
      } else {
        router.replace("/onboarding");
      }
    }
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center bg-[#FAFAF9]">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-merit-sky border-t-transparent" />
      </div>
    </div>
  );
}

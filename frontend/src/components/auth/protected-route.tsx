"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated, getUser, type AuthUser } from "@/lib/auth";

interface ProtectedRouteProps { children: React.ReactNode; allowedRoles?: AuthUser["role"][]; }

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const router = useRouter();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) { router.replace("/login"); return; }
    if (allowedRoles?.length) {
      const user = getUser();
      if (user && !allowedRoles.includes(user.role)) { router.replace("/dashboard"); return; }
    }
    setIsReady(true);
  }, [router, allowedRoles]);

  if (!isReady) {
    return (
      <div className="flex h-screen flex-col items-center justify-center bg-merit-cream">
        <img src="/logo.svg" alt="Merit" className="h-12 w-12 mb-4 drop-shadow-md" />
        <div className="flex items-center gap-1.5 mt-2">
          <div className="h-1.5 w-1.5 rounded-full bg-merit-sky animate-bounce [animation-delay:0ms]" />
          <div className="h-1.5 w-1.5 rounded-full bg-merit-sky animate-bounce [animation-delay:150ms]" />
          <div className="h-1.5 w-1.5 rounded-full bg-merit-sky animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

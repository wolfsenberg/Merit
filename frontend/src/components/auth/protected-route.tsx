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
      <div className="flex h-screen items-center justify-center bg-merit-cream">
        <div className="flex flex-col items-center gap-3">
          <div className="h-9 w-9 animate-spin rounded-full border-[3px] border-merit-sky border-t-transparent" />
          <p className="text-xs text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

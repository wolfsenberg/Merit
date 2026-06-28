"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated, getUser, type AuthUser } from "@/lib/auth";

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: AuthUser["role"][];
}

/**
 * Protected route wrapper that checks authentication and optional role access.
 * Redirects to /login if not authenticated.
 * Redirects to /dashboard if authenticated but role not allowed.
 */
export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }

    if (allowedRoles && allowedRoles.length > 0) {
      const user = getUser();
      if (user && !allowedRoles.includes(user.role)) {
        router.replace("/dashboard");
        return;
      }
    }

    setIsChecking(false);
  }, [router, allowedRoles]);

  if (isChecking) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gold-500 border-t-transparent" />
      </div>
    );
  }

  return <>{children}</>;
}

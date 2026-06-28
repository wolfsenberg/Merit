"use client";

import { getUser } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function ProgramsPage() {
  const router = useRouter();
  const user = getUser();

  useEffect(() => {
    // Redirect based on role
    if (user?.role === "org_admin" || user?.role === "super_admin") {
      router.replace("/programs/manage");
    } else {
      router.replace("/programs/browse");
    }
  }, [router, user]);

  return null;
}

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AdminDashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Admin Dashboard</h1>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card><CardHeader><CardTitle className="text-sm text-muted-foreground">Total Users</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">—</p></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm text-muted-foreground">Organizations</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">—</p></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm text-muted-foreground">Active Programs</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">—</p></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm text-muted-foreground">Total Transactions</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">—</p></CardContent></Card>
      </div>
      <p className="text-muted-foreground">Analytics data will be populated once the platform has active programs and users.</p>
    </div>
  );
}

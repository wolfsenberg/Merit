"use client";

import { usePrograms } from "@/hooks/use-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AnalyticsPage() {
  const { data, isLoading } = usePrograms();

  const programs = data?.items ?? [];
  const totalRecipients = programs.reduce((sum, p) => sum + p.current_recipients, 0);
  const totalFunded = programs.reduce((sum, p) => sum + p.total_funded, 0);
  const activePrograms = programs.filter((p) => p.status === "active").length;
  const complianceRate = programs.length > 0
    ? Math.round((activePrograms / programs.length) * 100)
    : 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Program Analytics</h1>

      {isLoading && (
        <div className="flex justify-center py-8">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gold-500 border-t-transparent" />
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Total Recipients</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{totalRecipients.toLocaleString()}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Total Funded</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">${totalFunded.toLocaleString()}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Active Programs</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{activePrograms}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Compliance Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{complianceRate}%</p>
          </CardContent>
        </Card>
      </div>

      {/* Program Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Programs Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          {programs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No programs to display.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="pb-2 font-medium">Program</th>
                    <th className="pb-2 font-medium">Status</th>
                    <th className="pb-2 font-medium">Recipients</th>
                    <th className="pb-2 font-medium">Total Funded</th>
                  </tr>
                </thead>
                <tbody>
                  {programs.map((program) => (
                    <tr key={program.id} className="border-b last:border-0">
                      <td className="py-2">{program.name}</td>
                      <td className="py-2">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs ${
                            program.status === "active"
                              ? "bg-green-100 text-green-700"
                              : "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {program.status}
                        </span>
                      </td>
                      <td className="py-2">{program.current_recipients}/{program.max_recipients}</td>
                      <td className="py-2">${program.total_funded.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

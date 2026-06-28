"use client";

import { useParams } from "next/navigation";
import { useProgram, useActivateProgram, usePauseProgram } from "@/hooks/use-api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ProgramDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const { data: program, isLoading } = useProgram(id);
  const activate = useActivateProgram();
  const pause = usePauseProgram();

  if (isLoading) return <div className="flex justify-center p-8"><div className="h-8 w-8 animate-spin rounded-full border-4 border-gold-500 border-t-transparent" /></div>;
  if (!program) return <div className="p-4 text-red-600">Program not found</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{program.name}</h1>
          <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-gold-50 text-gold-700 mt-1">
            {program.status}
          </span>
        </div>
        <div className="flex gap-2">
          {program.status === "draft" && (
            <Button onClick={() => activate.mutate(id)} className="bg-green-600 hover:bg-green-700" disabled={activate.isPending}>Activate</Button>
          )}
          {program.status === "active" && (
            <Button onClick={() => pause.mutate(id)} variant="outline" disabled={pause.isPending}>Pause</Button>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card><CardHeader><CardTitle className="text-sm text-muted-foreground">Recipients</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{program.current_recipients}/{program.max_recipients}</p></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm text-muted-foreground">Funding per Recipient</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">${program.funding_amount_per_recipient.toLocaleString()}</p></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm text-muted-foreground">Total Funded</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">${program.total_funded.toLocaleString()}</p></CardContent></Card>
      </div>

      <Card><CardHeader><CardTitle>Description</CardTitle></CardHeader><CardContent><p className="text-muted-foreground">{program.description}</p></CardContent></Card>
    </div>
  );
}

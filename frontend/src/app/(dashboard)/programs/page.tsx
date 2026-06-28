"use client";

import Link from "next/link";
import { usePrograms } from "@/hooks/use-api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ProgramsPage() {
  const { data, isLoading, error } = usePrograms();

  if (isLoading) return <div className="flex justify-center p-8"><div className="h-8 w-8 animate-spin rounded-full border-4 border-gold-500 border-t-transparent" /></div>;
  if (error) return <div className="p-4 text-red-600">Failed to load programs</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Programs</h1>
        <Button asChild className="bg-gold-500 hover:bg-gold-600">
          <Link href="/programs/new">Create Program</Link>
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {data?.items.map((program) => (
          <Link key={program.id} href={`/programs/${program.id}`}>
            <Card className="hover:border-gold-300 transition-colors">
              <CardHeader>
                <CardTitle className="text-lg">{program.name}</CardTitle>
                <span className="inline-flex items-center rounded-full px-2 py-1 text-xs font-medium bg-gold-50 text-gold-700">
                  {program.status}
                </span>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground line-clamp-2">{program.description}</p>
                <div className="mt-3 flex justify-between text-sm">
                  <span>{program.current_recipients}/{program.max_recipients} recipients</span>
                  <span>${program.total_funded.toLocaleString()} funded</span>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
        {data?.items.length === 0 && (
          <p className="col-span-full text-center text-muted-foreground py-8">No programs yet. Create your first program to get started.</p>
        )}
      </div>
    </div>
  );
}

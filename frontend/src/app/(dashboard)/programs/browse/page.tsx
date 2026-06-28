"use client";

import { usePrograms, useSubmitApplication } from "@/hooks/use-api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function BrowseProgramsPage() {
  const { data, isLoading, error } = usePrograms({ status: "active" });
  const submitApplication = useSubmitApplication();

  const handleApply = async (programId: string) => {
    await submitApplication.mutateAsync(programId);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Browse Programs</h1>
        <p className="text-sm text-muted-foreground">
          Discover active programs you can apply to
        </p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-8">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gold-500 border-t-transparent" />
        </div>
      )}

      {error && (
        <Card>
          <CardContent className="py-8 text-center text-red-600">
            Failed to load programs. Please try again.
          </CardContent>
        </Card>
      )}

      {data && data.items.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No active programs available at this time. Check back later.
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {data?.items.map((program) => (
          <Card key={program.id}>
            <CardHeader>
              <CardTitle className="text-lg">{program.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground line-clamp-3">
                {program.description}
              </p>
              <div className="space-y-1 text-sm">
                <p>
                  <strong>Funding:</strong> ${program.funding_amount_per_recipient.toLocaleString()} per recipient
                </p>
                <p>
                  <strong>Spots Available:</strong>{" "}
                  {program.max_recipients - program.current_recipients} of {program.max_recipients}
                </p>
                <p>
                  <strong>Start Date:</strong> {new Date(program.start_date).toLocaleDateString()}
                </p>
              </div>
              <Button
                className="w-full"
                onClick={() => handleApply(program.id)}
                disabled={submitApplication.isPending || program.current_recipients >= program.max_recipients}
              >
                {program.current_recipients >= program.max_recipients
                  ? "Program Full"
                  : submitApplication.isPending
                  ? "Applying..."
                  : "Apply"}
              </Button>
              {submitApplication.isSuccess && (
                <p className="text-center text-sm text-green-600">Application submitted!</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

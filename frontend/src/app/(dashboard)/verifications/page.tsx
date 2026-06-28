"use client";

import { useState } from "react";
import { useApplications, useVerifyDocument } from "@/hooks/use-api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function VerificationsPage() {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [notes, setNotes] = useState("");

  const { data, isLoading } = useApplications({ status: "pending_review" });
  const verifyDocument = useVerifyDocument();

  const handleVerify = async (documentId: string, approved: boolean) => {
    await verifyDocument.mutateAsync({ documentId, approved, notes: notes || undefined });
    setSelectedDocId(null);
    setNotes("");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Document Verifications</h1>
        <p className="text-sm text-muted-foreground">
          Review flagged documents requiring manual verification
        </p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-8">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gold-500 border-t-transparent" />
        </div>
      )}

      {data && data.items.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No documents pending review. All caught up!
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {data?.items.map((application) => (
          <Card key={application.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">
                  Application #{application.id.slice(0, 8)}
                </CardTitle>
                <span className="rounded-full bg-yellow-100 px-2 py-1 text-xs font-medium text-yellow-700">
                  {application.status}
                </span>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-sm text-muted-foreground">
                <p>Program: {application.program_id.slice(0, 8)}...</p>
                <p>Submitted: {new Date(application.submitted_at).toLocaleDateString()}</p>
              </div>

              {selectedDocId === application.id ? (
                <div className="space-y-3 rounded border p-3">
                  <div>
                    <Label htmlFor={`notes-${application.id}`}>Review Notes</Label>
                    <Input
                      id={`notes-${application.id}`}
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Add notes about your decision..."
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => handleVerify(application.id, true)}
                      disabled={verifyDocument.isPending}
                    >
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleVerify(application.id, false)}
                      disabled={verifyDocument.isPending}
                      className="text-red-600 hover:text-red-700"
                    >
                      Reject
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => { setSelectedDocId(null); setNotes(""); }}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setSelectedDocId(application.id)}
                >
                  Review Document
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

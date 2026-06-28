"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCreateProgram } from "@/hooks/use-api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function NewProgramPage() {
  const router = useRouter();
  const createProgram = useCreateProgram();
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: "", description: "", funding_amount_per_recipient: "", max_recipients: "",
    start_date: "", end_date: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createProgram.mutateAsync({
        name: formData.name,
        description: formData.description,
        organization_id: "",
        funding_amount_per_recipient: parseFloat(formData.funding_amount_per_recipient),
        max_recipients: parseInt(formData.max_recipients),
        start_date: formData.start_date,
        end_date: formData.end_date || undefined,
      });
      router.push("/programs");
    } catch {}
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">Create New Program</h1>
      <div className="flex gap-2 mb-6">
        {[1, 2, 3].map((s) => (
          <div key={s} className={`h-2 flex-1 rounded ${s <= step ? "bg-gold-500" : "bg-gray-200"}`} />
        ))}
      </div>

      <Card>
        <CardHeader><CardTitle>{step === 1 ? "Program Details" : step === 2 ? "Requirements" : "Review"}</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {step === 1 && (
              <>
                <div className="space-y-2"><Label>Program Name</Label><Input value={formData.name} onChange={(e) => setFormData(p => ({...p, name: e.target.value}))} required /></div>
                <div className="space-y-2"><Label>Description</Label><Input value={formData.description} onChange={(e) => setFormData(p => ({...p, description: e.target.value}))} required /></div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2"><Label>Funding per Recipient</Label><Input type="number" min="1" value={formData.funding_amount_per_recipient} onChange={(e) => setFormData(p => ({...p, funding_amount_per_recipient: e.target.value}))} required /></div>
                  <div className="space-y-2"><Label>Max Recipients</Label><Input type="number" min="1" value={formData.max_recipients} onChange={(e) => setFormData(p => ({...p, max_recipients: e.target.value}))} required /></div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2"><Label>Start Date</Label><Input type="date" value={formData.start_date} onChange={(e) => setFormData(p => ({...p, start_date: e.target.value}))} required /></div>
                  <div className="space-y-2"><Label>End Date (optional)</Label><Input type="date" value={formData.end_date} onChange={(e) => setFormData(p => ({...p, end_date: e.target.value}))} /></div>
                </div>
                <Button type="button" onClick={() => setStep(2)} className="bg-gold-500 hover:bg-gold-600">Next: Requirements</Button>
              </>
            )}
            {step === 2 && (
              <>
                <p className="text-muted-foreground">Requirements can be added after program creation.</p>
                <div className="flex gap-2">
                  <Button type="button" variant="outline" onClick={() => setStep(1)}>Back</Button>
                  <Button type="button" onClick={() => setStep(3)} className="bg-gold-500 hover:bg-gold-600">Next: Review</Button>
                </div>
              </>
            )}
            {step === 3 && (
              <>
                <div className="space-y-2 text-sm">
                  <p><strong>Name:</strong> {formData.name}</p>
                  <p><strong>Funding:</strong> ${formData.funding_amount_per_recipient} per recipient</p>
                  <p><strong>Max Recipients:</strong> {formData.max_recipients}</p>
                  <p><strong>Start:</strong> {formData.start_date}</p>
                </div>
                <div className="flex gap-2">
                  <Button type="button" variant="outline" onClick={() => setStep(2)}>Back</Button>
                  <Button type="submit" className="bg-gold-500 hover:bg-gold-600" disabled={createProgram.isPending}>
                    {createProgram.isPending ? "Creating..." : "Create Program"}
                  </Button>
                </div>
              </>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import { useState } from "react";
import { CheckCircle2, XCircle, Clock, User, FileText, ExternalLink } from "lucide-react";

interface VerificationRequest {
  id: string;
  studentName: string;
  email: string;
  scholarship: string;
  submittedAt: string;
  documents: string[];
  status: "pending" | "approved" | "rejected";
}

const requests: VerificationRequest[] = [
  { id: "v1", studentName: "Maria Santos", email: "maria.santos@up.edu.ph", scholarship: "DOST-SEI Merit", submittedAt: "Jun 28, 2026", documents: ["Grade slip", "Enrollment cert", "Valid ID"], status: "pending" },
  { id: "v2", studentName: "Juan Reyes", email: "j.reyes@ust.edu.ph", scholarship: "DOST-SEI Merit", submittedAt: "Jun 27, 2026", documents: ["Grade slip", "Enrollment cert"], status: "pending" },
  { id: "v3", studentName: "Ana Cruz", email: "ana.cruz@admu.edu.ph", scholarship: "CHED Tulong Dunong", submittedAt: "Jun 26, 2026", documents: ["Grade slip", "Income cert", "Enrollment cert"], status: "pending" },
];

export default function VerificationsPage() {
  const [items, setItems] = useState(requests);

  const handleApprove = (id: string) => {
    setItems(prev => prev.map(r => r.id === id ? { ...r, status: "approved" as const } : r));
  };

  const handleReject = (id: string) => {
    setItems(prev => prev.map(r => r.id === id ? { ...r, status: "rejected" as const } : r));
  };

  const pending = items.filter(r => r.status === "pending");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Verification Queue</h1>
        <p className="mt-1 text-[13px] text-gray-400">{pending.length} scholars awaiting document verification</p>
      </div>

      <div className="space-y-3">
        {items.map(req => (
          <div key={req.id} className="rounded-xl border border-black/[0.04] bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#FAFAF9] text-[11px] font-semibold text-gray-500">
                  {req.studentName.split(" ").map(n => n[0]).join("")}
                </div>
                <div>
                  <p className="text-[13px] font-medium text-gray-900">{req.studentName}</p>
                  <p className="text-[11px] text-gray-400">{req.email} — {req.scholarship}</p>
                </div>
              </div>
              {req.status === "approved" && <span className="flex items-center gap-1 text-[10px] font-medium text-emerald-600"><CheckCircle2 className="h-3 w-3" /> Approved</span>}
              {req.status === "rejected" && <span className="flex items-center gap-1 text-[10px] font-medium text-red-500"><XCircle className="h-3 w-3" /> Rejected</span>}
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              {req.documents.map(doc => (
                <span key={doc} className="flex items-center gap-1 rounded-md bg-[#FAFAF9] border border-black/[0.04] px-2 py-1 text-[10px] text-gray-600">
                  <FileText className="h-3 w-3 text-gray-400" /> {doc}
                </span>
              ))}
            </div>

            {req.status === "pending" && (
              <div className="mt-3 flex items-center gap-2">
                <button onClick={() => handleApprove(req.id)} className="flex items-center gap-1.5 rounded-lg bg-emerald-50 border border-emerald-100 px-3 py-2 text-[11px] font-medium text-emerald-700 hover:bg-emerald-100 transition-colors">
                  <CheckCircle2 className="h-3.5 w-3.5" /> Approve & Disburse
                </button>
                <button onClick={() => handleReject(req.id)} className="flex items-center gap-1.5 rounded-lg bg-red-50 border border-red-100 px-3 py-2 text-[11px] font-medium text-red-600 hover:bg-red-100 transition-colors">
                  <XCircle className="h-3.5 w-3.5" /> Reject
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

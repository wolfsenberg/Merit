"use client";

import { useState } from "react";
import { Upload, FileText, CheckCircle2, Clock, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Document {
  id: string;
  name: string;
  type: string;
  status: "verified" | "processing" | "pending" | "rejected";
  uploadedAt: string;
  confidence?: number;
}

const mockDocuments: Document[] = [
  { id: "1", name: "Grade_Slip_2024_1st_Sem.pdf", type: "Grade Slip", status: "verified", uploadedAt: "Jun 20, 2026", confidence: 0.94 },
  { id: "2", name: "Enrollment_Certificate.pdf", type: "Enrollment Form", status: "verified", uploadedAt: "Jun 20, 2026", confidence: 0.89 },
  { id: "3", name: "Valid_ID_Scan.jpg", type: "ID Document", status: "verified", uploadedAt: "Jun 20, 2026", confidence: 0.97 },
];

export default function DocumentsPage() {
  const [documents] = useState<Document[]>(mockDocuments);

  const statusConfig = {
    verified: { icon: CheckCircle2, label: "Verified", color: "text-emerald-600 bg-emerald-50 border-emerald-100" },
    processing: { icon: Clock, label: "Processing", color: "text-sky-600 bg-sky-50 border-sky-100" },
    pending: { icon: Clock, label: "Pending", color: "text-gray-500 bg-gray-50 border-gray-100" },
    rejected: { icon: AlertCircle, label: "Rejected", color: "text-red-600 bg-red-50 border-red-100" },
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Documents</h1>
          <p className="mt-1 text-[13px] text-gray-400">{documents.length} documents uploaded</p>
        </div>
        <Button className="h-9 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-[12px] font-medium px-4 flex items-center gap-1.5">
          <Upload className="h-3.5 w-3.5" /> Upload
        </Button>
      </div>

      <div className="space-y-2.5">
        {documents.map((doc) => {
          const config = statusConfig[doc.status];
          const StatusIcon = config.icon;
          return (
            <div key={doc.id} className="flex items-center gap-3 rounded-xl border border-black/[0.04] bg-white p-4">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#FAFAF9]">
                <FileText className="h-4 w-4 text-gray-400" strokeWidth={1.5} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[13px] font-medium text-gray-900 truncate">{doc.name}</p>
                <p className="text-[11px] text-gray-400">{doc.type} — {doc.uploadedAt}</p>
              </div>
              <div className={`flex items-center gap-1 rounded-md border px-2 py-0.5 ${config.color}`}>
                <StatusIcon className="h-3 w-3" />
                <span className="text-[10px] font-medium">{config.label}</span>
              </div>
              {doc.confidence && (
                <span className="hidden md:block text-[10px] text-gray-400">{Math.round(doc.confidence * 100)}% confidence</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

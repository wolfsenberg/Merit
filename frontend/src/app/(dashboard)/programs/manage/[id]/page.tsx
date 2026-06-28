"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, CheckCircle2, XCircle, Clock, Upload, Users, Banknote, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Scholar {
  id: string;
  name: string;
  email: string;
  studentId: string;
  university: string;
  status: "pending" | "approved" | "rejected";
  appliedDate: string;
  amount: string;
}

const mockScholars: Scholar[] = [
  { id: "s1", name: "Maria Santos", email: "maria.santos@up.edu.ph", studentId: "2022-04521", university: "UP Diliman", status: "pending", appliedDate: "Jun 15, 2026", amount: "PHP 10,000" },
  { id: "s2", name: "Juan Reyes", email: "j.reyes@ust.edu.ph", studentId: "2021-89032", university: "UST", status: "pending", appliedDate: "Jun 16, 2026", amount: "PHP 10,000" },
  { id: "s3", name: "Ana Cruz", email: "ana.cruz@admu.edu.ph", studentId: "2023-12890", university: "Ateneo de Manila", status: "pending", appliedDate: "Jun 17, 2026", amount: "PHP 10,000" },
  { id: "s4", name: "Carlos Garcia", email: "c.garcia@dlsu.edu.ph", studentId: "2022-56781", university: "De La Salle University", status: "pending", appliedDate: "Jun 18, 2026", amount: "PHP 10,000" },
  { id: "s5", name: "Demo User", email: "demo@merit.app", studentId: "2023-00001", university: "PUP Manila", status: "approved", appliedDate: "Jun 10, 2026", amount: "PHP 10,000" },
  { id: "s6", name: "Grace Lim", email: "g.lim@tup.edu.ph", studentId: "2022-33445", university: "TUP Manila", status: "approved", appliedDate: "Jun 8, 2026", amount: "PHP 10,000" },
];

export default function ManageScholarshipPage() {
  const router = useRouter();
  const params = useParams();
  const [scholars, setScholars] = useState(mockScholars);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<"pending" | "approved" | "all">("pending");

  const programName = params.id === "dost-sei" ? "DOST-SEI Merit Scholarship" : "CHED Tulong Dunong Program";

  const handleApprove = (scholarId: string) => {
    setScholars(prev => prev.map(s => s.id === scholarId ? { ...s, status: "approved" as const } : s));
  };

  const handleReject = (scholarId: string) => {
    setScholars(prev => prev.map(s => s.id === scholarId ? { ...s, status: "rejected" as const } : s));
  };

  const handleBatchApprove = () => {
    setScholars(prev => prev.map(s => s.status === "pending" ? { ...s, status: "approved" as const } : s));
  };

  const filtered = scholars
    .filter(s => activeTab === "all" ? true : s.status === activeTab)
    .filter(s => searchQuery ? s.name.toLowerCase().includes(searchQuery.toLowerCase()) || s.email.toLowerCase().includes(searchQuery.toLowerCase()) || s.studentId.includes(searchQuery) : true);

  const pendingCount = scholars.filter(s => s.status === "pending").length;
  const approvedCount = scholars.filter(s => s.status === "approved").length;

  return (
    <div className="space-y-6">
      {/* Back */}
      <button onClick={() => router.push("/programs/manage")} className="flex items-center gap-1.5 text-[13px] text-gray-400 hover:text-gray-600 transition-colors">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to programs
      </button>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-[20px] font-semibold tracking-tight text-gray-900">{programName}</h1>
          <div className="flex items-center gap-4 mt-1.5 text-[11px] text-gray-400">
            <span className="flex items-center gap-1"><Users className="h-3 w-3" />{approvedCount} approved</span>
            <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{pendingCount} pending</span>
            <span className="flex items-center gap-1"><Banknote className="h-3 w-3" />PHP {(approvedCount * 10000).toLocaleString()} disbursed</span>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" className="h-8 rounded-lg border border-black/[0.06] text-[11px] font-medium px-3 flex items-center gap-1.5">
            <Upload className="h-3 w-3" /> Import CSV
          </Button>
          {pendingCount > 0 && (
            <Button onClick={handleBatchApprove} className="h-8 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-medium px-3">
              Approve All ({pendingCount})
            </Button>
          )}
        </div>
      </div>

      {/* Search + Tabs */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
          <Input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Search by name, email, or student ID" className="h-9 pl-9 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[12px]" />
        </div>
        <div className="flex items-center gap-1 rounded-lg bg-white border border-black/[0.04] p-0.5">
          <button onClick={() => setActiveTab("pending")} className={`rounded-md px-2.5 py-1 text-[11px] font-medium ${activeTab === "pending" ? "bg-amber-50 text-amber-700" : "text-gray-500"}`}>Pending ({pendingCount})</button>
          <button onClick={() => setActiveTab("approved")} className={`rounded-md px-2.5 py-1 text-[11px] font-medium ${activeTab === "approved" ? "bg-emerald-50 text-emerald-700" : "text-gray-500"}`}>Approved ({approvedCount})</button>
          <button onClick={() => setActiveTab("all")} className={`rounded-md px-2.5 py-1 text-[11px] font-medium ${activeTab === "all" ? "bg-gray-100 text-gray-700" : "text-gray-500"}`}>All</button>
        </div>
      </div>

      {/* Scholar list */}
      <div className="rounded-xl border border-black/[0.04] bg-white overflow-hidden">
        {filtered.length === 0 ? (
          <div className="py-12 text-center text-[13px] text-gray-400">No scholars found.</div>
        ) : (
          filtered.map((scholar, idx) => (
            <div key={scholar.id} className={`flex items-center gap-3 px-4 py-3 ${idx < filtered.length - 1 ? "border-b border-black/[0.03]" : ""}`}>
              {/* Avatar */}
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#FAFAF9] text-[11px] font-semibold text-gray-500 shrink-0">
                {scholar.name.split(" ").map(n => n[0]).join("")}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <p className="text-[13px] font-medium text-gray-900">{scholar.name}</p>
                <div className="flex items-center gap-2 text-[10px] text-gray-400 mt-0.5">
                  <span>{scholar.email}</span>
                  <span className="text-gray-300">|</span>
                  <span>{scholar.studentId}</span>
                  <span className="text-gray-300">|</span>
                  <span>{scholar.university}</span>
                </div>
              </div>

              {/* Status / Actions */}
              {scholar.status === "pending" && (
                <div className="flex items-center gap-1.5 shrink-0">
                  <button onClick={() => handleApprove(scholar.id)} className="flex h-7 items-center gap-1 rounded-md bg-emerald-50 border border-emerald-100 px-2.5 text-[10px] font-medium text-emerald-700 hover:bg-emerald-100 transition-colors">
                    <CheckCircle2 className="h-3 w-3" /> Approve
                  </button>
                  <button onClick={() => handleReject(scholar.id)} className="flex h-7 items-center gap-1 rounded-md bg-red-50 border border-red-100 px-2.5 text-[10px] font-medium text-red-600 hover:bg-red-100 transition-colors">
                    <XCircle className="h-3 w-3" /> Reject
                  </button>
                </div>
              )}
              {scholar.status === "approved" && (
                <span className="flex items-center gap-1 text-[10px] font-medium text-emerald-600 shrink-0">
                  <CheckCircle2 className="h-3 w-3" /> Approved &mdash; {scholar.amount} sent
                </span>
              )}
              {scholar.status === "rejected" && (
                <span className="flex items-center gap-1 text-[10px] font-medium text-red-500 shrink-0">
                  <XCircle className="h-3 w-3" /> Rejected
                </span>
              )}
            </div>
          ))
        )}
      </div>

      {/* Info box */}
      <div className="rounded-xl border border-black/[0.04] bg-[#FAFAF9] p-4 text-[11px] text-gray-500 leading-relaxed">
        <p className="font-medium text-gray-700 mb-1">How disbursement works:</p>
        <p>When you approve a scholar, funds are automatically transferred from the scholarship pool to their Merit wallet via the Stellar network. The transaction is recorded on-chain and the student is notified instantly.</p>
      </div>
    </div>
  );
}

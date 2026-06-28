"use client";

import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { CheckCircle2, Upload, ArrowLeft, FileText, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const scholarshipData: Record<string, { name: string; org: string; requirements: string[] }> = {
  "dost-sei": { name: "DOST-SEI Merit Scholarship", org: "Department of Science and Technology", requirements: ["Grade slip (latest semester)", "Enrollment certificate", "Valid ID"] },
  "sm-foundation": { name: "SM Foundation Scholarship", org: "SM Foundation Inc.", requirements: ["Grade slip (GWA 2.0 or better)", "Family income certificate", "Enrollment form", "Valid ID"] },
  "quezon-city": { name: "QC Iskolar ng Bayan", org: "Quezon City LGU", requirements: ["Proof of QC residency (3+ years)", "Grade slip", "Enrollment certificate"] },
  "ched-tulong": { name: "CHED Tulong Dunong", org: "Commission on Higher Education", requirements: ["Grade slip", "Certificate of enrollment in priority course", "Valid ID"] },
  "makati-city": { name: "Makati City College Grant", org: "City Government of Makati", requirements: ["Proof of Makati residency (5+ years)", "Grade slip (GWA 2.0+)", "Birth certificate", "Enrollment form"] },
  "pasig-city": { name: "Pasig City Educational Aid", org: "City Government of Pasig", requirements: ["Proof of Pasig residency", "Grade slip", "Enrollment certificate"] },
};

type Step = "info" | "documents" | "review" | "submitted";

export default function ApplyScholarshipPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;
  const scholarship = scholarshipData[id];

  const [step, setStep] = useState<Step>("info");
  const [formData, setFormData] = useState({
    fullName: "", studentId: "", university: "", course: "", yearLevel: "", contactNumber: "",
  });
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);

  if (!scholarship) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <AlertCircle className="h-8 w-8 text-gray-300 mb-3" />
        <p className="text-[14px] text-gray-500">Scholarship not found</p>
        <button onClick={() => router.push("/programs/browse")} className="mt-3 text-[13px] font-medium text-merit-gold">Back to scholarships</button>
      </div>
    );
  }

  const handleFileUpload = (fileName: string) => {
    if (!uploadedFiles.includes(fileName)) {
      setUploadedFiles([...uploadedFiles, fileName]);
    }
  };

  const handleSubmit = () => {
    setStep("submitted");
  };

  return (
    <div className="space-y-6">
      {/* Back nav */}
      <button onClick={() => router.push("/programs/browse")} className="flex items-center gap-1.5 text-[13px] text-gray-400 hover:text-gray-600 transition-colors">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to scholarships
      </button>

      {/* Header */}
      <div>
        <h1 className="text-[20px] font-semibold tracking-tight text-gray-900">{scholarship.name}</h1>
        <p className="text-[12px] text-gray-400 mt-0.5">{scholarship.org}</p>
      </div>

      {/* Progress */}
      {step !== "submitted" && (
        <div className="flex items-center gap-2">
          {(["info", "documents", "review"] as Step[]).map((s, idx) => (
            <div key={s} className="flex items-center gap-2">
              <div className={`flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold ${
                step === s ? "bg-merit-gold text-white" :
                (["info", "documents", "review"].indexOf(step) > idx) ? "bg-emerald-500 text-white" :
                "bg-gray-100 text-gray-400"
              }`}>
                {["info", "documents", "review"].indexOf(step) > idx ? <CheckCircle2 className="h-3 w-3" /> : idx + 1}
              </div>
              {idx < 2 && <div className={`h-[2px] w-8 rounded ${["info", "documents", "review"].indexOf(step) > idx ? "bg-emerald-500" : "bg-gray-100"}`} />}
            </div>
          ))}
          <span className="text-[11px] text-gray-400 ml-2">
            {step === "info" ? "Personal Info" : step === "documents" ? "Upload Documents" : "Review & Submit"}
          </span>
        </div>
      )}

      {/* Step 1: Personal Info */}
      {step === "info" && (
        <div className="rounded-xl border border-black/[0.04] bg-white p-5 space-y-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Full Name</Label>
              <Input value={formData.fullName} onChange={e => setFormData(p => ({...p, fullName: e.target.value}))} placeholder="Juan Dela Cruz" className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[13px]" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Student ID</Label>
              <Input value={formData.studentId} onChange={e => setFormData(p => ({...p, studentId: e.target.value}))} placeholder="2023-12345" className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[13px]" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">University</Label>
              <Input value={formData.university} onChange={e => setFormData(p => ({...p, university: e.target.value}))} placeholder="University of the Philippines" className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[13px]" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Course</Label>
              <Input value={formData.course} onChange={e => setFormData(p => ({...p, course: e.target.value}))} placeholder="BS Computer Science" className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[13px]" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Year Level</Label>
              <Input value={formData.yearLevel} onChange={e => setFormData(p => ({...p, yearLevel: e.target.value}))} placeholder="3rd Year" className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[13px]" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Contact Number</Label>
              <Input value={formData.contactNumber} onChange={e => setFormData(p => ({...p, contactNumber: e.target.value}))} placeholder="09XX XXX XXXX" className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[13px]" />
            </div>
          </div>
          <Button onClick={() => setStep("documents")} className="w-full h-10 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-[13px] font-medium mt-2">
            Continue to Documents
          </Button>
        </div>
      )}

      {/* Step 2: Upload Documents */}
      {step === "documents" && (
        <div className="rounded-xl border border-black/[0.04] bg-white p-5 space-y-4">
          <p className="text-[12px] text-gray-500">Upload the following required documents:</p>
          <div className="space-y-2.5">
            {scholarship.requirements.map((req) => {
              const isUploaded = uploadedFiles.includes(req);
              return (
                <div key={req} className={`flex items-center gap-3 rounded-lg border p-3 transition-all ${isUploaded ? "border-emerald-200 bg-emerald-50/50" : "border-black/[0.06] bg-[#FAFAF9]"}`}>
                  {isUploaded ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                  ) : (
                    <FileText className="h-4 w-4 text-gray-300 shrink-0" />
                  )}
                  <span className="flex-1 text-[12px] text-gray-700">{req}</span>
                  {!isUploaded ? (
                    <button onClick={() => handleFileUpload(req)} className="flex items-center gap-1 rounded-md bg-white border border-black/[0.08] px-2.5 py-1 text-[11px] font-medium text-gray-600 hover:border-merit-gold/30 transition-colors">
                      <Upload className="h-3 w-3" /> Upload
                    </button>
                  ) : (
                    <span className="text-[11px] text-emerald-600 font-medium">Done</span>
                  )}
                </div>
              );
            })}
          </div>
          <div className="flex gap-2 mt-2">
            <Button onClick={() => setStep("info")} variant="ghost" className="flex-1 h-10 rounded-lg text-[13px]">Back</Button>
            <Button onClick={() => setStep("review")} disabled={uploadedFiles.length < scholarship.requirements.length} className="flex-1 h-10 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-[13px] font-medium">
              Review Application
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Review */}
      {step === "review" && (
        <div className="rounded-xl border border-black/[0.04] bg-white p-5 space-y-4">
          <div className="space-y-3">
            <h3 className="text-[12px] font-medium text-gray-400 uppercase tracking-wide">Application Summary</h3>
            <div className="grid grid-cols-2 gap-2 text-[12px]">
              <div className="text-gray-400">Name</div><div className="text-gray-900 font-medium">{formData.fullName || "—"}</div>
              <div className="text-gray-400">Student ID</div><div className="text-gray-900 font-medium">{formData.studentId || "—"}</div>
              <div className="text-gray-400">University</div><div className="text-gray-900 font-medium">{formData.university || "—"}</div>
              <div className="text-gray-400">Course</div><div className="text-gray-900 font-medium">{formData.course || "—"}</div>
              <div className="text-gray-400">Year</div><div className="text-gray-900 font-medium">{formData.yearLevel || "—"}</div>
              <div className="text-gray-400">Contact</div><div className="text-gray-900 font-medium">{formData.contactNumber || "—"}</div>
            </div>
            <div className="border-t border-black/[0.04] pt-3">
              <p className="text-[11px] text-gray-400 mb-2">Documents uploaded: {uploadedFiles.length}/{scholarship.requirements.length}</p>
              {uploadedFiles.map(f => (
                <div key={f} className="flex items-center gap-2 text-[11px] text-emerald-700 mb-1">
                  <CheckCircle2 className="h-3 w-3" /> {f}
                </div>
              ))}
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setStep("documents")} variant="ghost" className="flex-1 h-10 rounded-lg text-[13px]">Back</Button>
            <Button onClick={handleSubmit} className="flex-1 h-10 rounded-lg bg-merit-gold hover:bg-gold-500 text-white text-[13px] font-medium shadow-sm shadow-merit-gold/20">
              Submit Application
            </Button>
          </div>
        </div>
      )}

      {/* Step 4: Submitted */}
      {step === "submitted" && (
        <div className="rounded-xl border border-black/[0.04] bg-white p-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-50 border border-emerald-100">
            <CheckCircle2 className="h-6 w-6 text-emerald-500" />
          </div>
          <h2 className="text-[18px] font-semibold text-gray-900">Application Submitted</h2>
          <p className="mt-2 text-[13px] text-gray-500 max-w-[300px] mx-auto">
            Your application for {scholarship.name} has been submitted. AI verification will begin shortly.
          </p>
          <p className="mt-1 text-[11px] text-gray-400">You&apos;ll be notified once your documents are verified.</p>
          <Button onClick={() => router.push("/programs/browse")} className="mt-6 h-10 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-[13px] font-medium px-6">
            Back to Scholarships
          </Button>
        </div>
      )}
    </div>
  );
}

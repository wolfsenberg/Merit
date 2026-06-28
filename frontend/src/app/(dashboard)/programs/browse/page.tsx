"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { MapPin, Calendar, Users, Banknote, ChevronRight, CheckCircle2, Clock } from "lucide-react";

interface Scholarship {
  id: string;
  name: string;
  organization: string;
  location: string;
  amount: string;
  slots: number;
  slotsLeft: number;
  deadline: string;
  requirements: string[];
  status: "open" | "applied" | "closed";
  description: string;
}

const scholarships: Scholarship[] = [
  {
    id: "dost-sei",
    name: "DOST-SEI Merit Scholarship",
    organization: "Department of Science and Technology",
    location: "Nationwide",
    amount: "PHP 10,000/sem",
    slots: 5000,
    slotsLeft: 1247,
    deadline: "Aug 30, 2026",
    requirements: ["GWA of 1.75 or better", "Enrolled in S&T course", "Filipino citizen"],
    status: "applied",
    description: "Full tuition and monthly stipend for students pursuing science and technology courses in state universities.",
  },
  {
    id: "sm-foundation",
    name: "SM Foundation Scholarship",
    organization: "SM Foundation Inc.",
    location: "Metro Manila, Cebu, Davao",
    amount: "PHP 15,000/sem",
    slots: 200,
    slotsLeft: 43,
    deadline: "Jul 15, 2026",
    requirements: ["GWA of 2.0 or better", "Family income below PHP 300K/yr", "Full-time student"],
    status: "open",
    description: "Covers tuition, books, and monthly allowance for financially disadvantaged but academically talented students.",
  },
  {
    id: "quezon-city",
    name: "QC Iskolar ng Bayan",
    organization: "Quezon City LGU",
    location: "Quezon City",
    amount: "PHP 8,000/sem",
    slots: 1000,
    slotsLeft: 312,
    deadline: "Sep 1, 2026",
    requirements: ["QC resident for 3+ years", "GWA of 2.5 or better", "Enrolled in any SUC"],
    status: "open",
    description: "Educational assistance for Quezon City residents enrolled in state universities and colleges.",
  },
  {
    id: "ched-tulong",
    name: "CHED Tulong Dunong",
    organization: "Commission on Higher Education",
    location: "Nationwide",
    amount: "PHP 20,000/yr",
    slots: 3000,
    slotsLeft: 890,
    deadline: "Aug 15, 2026",
    requirements: ["Filipino citizen", "Not a recipient of other govt scholarship", "Enrolled in priority course"],
    status: "open",
    description: "Government financial assistance for students enrolled in priority courses identified by CHED.",
  },
  {
    id: "makati-city",
    name: "Makati City College Grant",
    organization: "City Government of Makati",
    location: "Makati City",
    amount: "Full tuition + PHP 5,000/mo",
    slots: 500,
    slotsLeft: 78,
    deadline: "Jul 30, 2026",
    requirements: ["Makati resident for 5+ years", "Not more than 25 years old", "GWA of 2.0 or better"],
    status: "open",
    description: "Complete educational package including tuition, monthly stipend, and book allowance for Makati residents.",
  },
  {
    id: "pasig-city",
    name: "Pasig City Educational Aid",
    organization: "City Government of Pasig",
    location: "Pasig City",
    amount: "PHP 6,000/sem",
    slots: 800,
    slotsLeft: 215,
    deadline: "Aug 20, 2026",
    requirements: ["Pasig resident", "Currently enrolled", "GWA of 2.5 or better"],
    status: "open",
    description: "Semestral educational assistance for Pasig residents pursuing college education.",
  },
];

export default function BrowseScholarshipsPage() {
  const router = useRouter();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Explore Scholarships</h1>
        <p className="mt-1 text-[13px] text-gray-400">{scholarships.filter(s => s.status === "open").length} programs accepting applications</p>
      </div>

      <div className="space-y-3">
        {scholarships.map((scholarship) => (
          <ScholarshipCard
            key={scholarship.id}
            scholarship={scholarship}
            onApply={() => router.push(`/programs/apply/${scholarship.id}`)}
          />
        ))}
      </div>
    </div>
  );
}

function ScholarshipCard({ scholarship, onApply }: { scholarship: Scholarship; onApply: () => void }) {
  const percentFilled = Math.round(((scholarship.slots - scholarship.slotsLeft) / scholarship.slots) * 100);

  return (
    <div className="rounded-xl border border-black/[0.04] bg-white p-4 md:p-5 transition-all hover:border-black/[0.08]">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-[14px] font-semibold text-gray-900">{scholarship.name}</h3>
          <p className="text-[12px] text-gray-400 mt-0.5">{scholarship.organization}</p>
        </div>
        {scholarship.status === "applied" && (
          <span className="flex items-center gap-1 rounded-md bg-emerald-50 border border-emerald-100 px-2 py-0.5 text-[11px] font-medium text-emerald-700 shrink-0">
            <CheckCircle2 className="h-3 w-3" /> Applied
          </span>
        )}
      </div>

      <p className="mt-2 text-[12px] text-gray-500 leading-relaxed line-clamp-2">{scholarship.description}</p>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px] text-gray-400">
        <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{scholarship.location}</span>
        <span className="flex items-center gap-1"><Banknote className="h-3 w-3" />{scholarship.amount}</span>
        <span className="flex items-center gap-1"><Users className="h-3 w-3" />{scholarship.slotsLeft} slots left</span>
        <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />Due {scholarship.deadline}</span>
      </div>

      {/* Progress bar */}
      <div className="mt-3">
        <div className="h-1 rounded-full bg-gray-100 overflow-hidden">
          <div className="h-full rounded-full bg-merit-gold/60 transition-all" style={{ width: `${percentFilled}%` }} />
        </div>
        <p className="text-[10px] text-gray-400 mt-1">{percentFilled}% slots filled</p>
      </div>

      {/* Action */}
      {scholarship.status === "open" && (
        <button
          onClick={onApply}
          className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg border border-black/[0.06] bg-[#FAFAF9] py-2 text-[12px] font-medium text-gray-700 hover:bg-merit-gold/5 hover:border-merit-gold/20 hover:text-gray-900 transition-all"
        >
          Apply Now <ChevronRight className="h-3.5 w-3.5" />
        </button>
      )}
      {scholarship.status === "applied" && (
        <button
          onClick={() => {}}
          className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg bg-emerald-50 border border-emerald-100 py-2 text-[12px] font-medium text-emerald-700"
        >
          <Clock className="h-3.5 w-3.5" /> Awaiting Verification
        </button>
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { MapPin, Calendar, Users, Banknote, ChevronRight, CheckCircle2, Clock, Globe, Building2 } from "lucide-react";

type ScholarshipScope = "all" | "national" | "city";

interface Scholarship {
  id: string;
  name: string;
  organization: string;
  location: string;
  scope: "national" | "city";
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
    scope: "national",
    amount: "PHP 10,000/sem",
    slots: 5000,
    slotsLeft: 1247,
    deadline: "Aug 30, 2026",
    requirements: ["GWA of 1.75 or better", "Enrolled in S&T course", "Filipino citizen"],
    status: "applied",
    description: "Full tuition and monthly stipend for students pursuing science and technology courses in state universities.",
  },
  {
    id: "ched-tulong",
    name: "CHED Tulong Dunong",
    organization: "Commission on Higher Education",
    location: "Nationwide",
    scope: "national",
    amount: "PHP 20,000/yr",
    slots: 3000,
    slotsLeft: 890,
    deadline: "Aug 15, 2026",
    requirements: ["Filipino citizen", "Not a recipient of other govt scholarship", "Enrolled in priority course"],
    status: "open",
    description: "Government financial assistance for students enrolled in priority courses identified by CHED.",
  },
  {
    id: "sm-foundation",
    name: "SM Foundation Scholarship",
    organization: "SM Foundation Inc.",
    location: "Nationwide",
    scope: "national",
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
    scope: "city",
    amount: "PHP 8,000/sem",
    slots: 1000,
    slotsLeft: 312,
    deadline: "Sep 1, 2026",
    requirements: ["QC resident for 3+ years", "GWA of 2.5 or better", "Enrolled in any SUC"],
    status: "open",
    description: "Educational assistance for Quezon City residents enrolled in state universities and colleges.",
  },
  {
    id: "makati-city",
    name: "Makati City College Grant",
    organization: "City Government of Makati",
    location: "Makati City",
    scope: "city",
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
    scope: "city",
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
  const [activeTab, setActiveTab] = useState<ScholarshipScope>("all");

  const filtered = activeTab === "all" ? scholarships : scholarships.filter(s => s.scope === activeTab);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Explore Scholarships</h1>
        <p className="mt-1 text-[13px] text-gray-400">{filtered.filter(s => s.status === "open").length} programs accepting applications</p>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1 rounded-lg bg-white border border-black/[0.04] p-1 w-fit">
        <TabButton active={activeTab === "all"} onClick={() => setActiveTab("all")} label="All" count={scholarships.length} />
        <TabButton active={activeTab === "national"} onClick={() => setActiveTab("national")} label="National" count={scholarships.filter(s => s.scope === "national").length} icon={<Globe className="h-3 w-3" />} />
        <TabButton active={activeTab === "city"} onClick={() => setActiveTab("city")} label="City-based" count={scholarships.filter(s => s.scope === "city").length} icon={<Building2 className="h-3 w-3" />} />
      </div>

      {/* List */}
      <div className="space-y-3">
        {filtered.map((scholarship) => (
          <ScholarshipCard
            key={scholarship.id}
            scholarship={scholarship}
            onApply={() => router.push(`/programs/apply/${scholarship.id}`)}
          />
        ))}
        {filtered.length === 0 && (
          <div className="py-12 text-center text-[13px] text-gray-400">No scholarships found in this category.</div>
        )}
      </div>
    </div>
  );
}

function TabButton({ active, onClick, label, count, icon }: { active: boolean; onClick: () => void; label: string; count: number; icon?: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[12px] font-medium transition-all ${
        active ? "bg-merit-gold/10 text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
      }`}
    >
      {icon}
      {label}
      <span className={`text-[10px] ${active ? "text-merit-gold" : "text-gray-400"}`}>{count}</span>
    </button>
  );
}

function ScholarshipCard({ scholarship, onApply }: { scholarship: Scholarship; onApply: () => void }) {
  const percentFilled = Math.round(((scholarship.slots - scholarship.slotsLeft) / scholarship.slots) * 100);

  return (
    <div className="rounded-xl border border-black/[0.04] bg-white p-4 md:p-5 transition-all hover:border-black/[0.08]">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-[14px] font-semibold text-gray-900">{scholarship.name}</h3>
            <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide ${
              scholarship.scope === "national" ? "bg-sky-50 text-sky-700 border border-sky-100" : "bg-amber-50 text-amber-700 border border-amber-100"
            }`}>
              {scholarship.scope === "national" ? "National" : "City"}
            </span>
          </div>
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

      <div className="mt-3">
        <div className="h-1 rounded-full bg-gray-100 overflow-hidden">
          <div className="h-full rounded-full bg-merit-gold/60 transition-all" style={{ width: `${percentFilled}%` }} />
        </div>
        <p className="text-[10px] text-gray-400 mt-1">{percentFilled}% slots filled</p>
      </div>

      {scholarship.status === "open" && (
        <button onClick={onApply} className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg border border-black/[0.06] bg-[#FAFAF9] py-2 text-[12px] font-medium text-gray-700 hover:bg-merit-gold/5 hover:border-merit-gold/20 hover:text-gray-900 transition-all">
          Apply Now <ChevronRight className="h-3.5 w-3.5" />
        </button>
      )}
      {scholarship.status === "applied" && (
        <button className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg bg-emerald-50 border border-emerald-100 py-2 text-[12px] font-medium text-emerald-700">
          <Clock className="h-3.5 w-3.5" /> Awaiting Verification
        </button>
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import { MapPin, Calendar, Users, Banknote, ExternalLink, Globe, Building2, CheckCircle2, Clock } from "lucide-react";

type ScholarshipScope = "all" | "national" | "city";

interface Scholarship {
  id: string;
  name: string;
  organization: string;
  location: string;
  scope: "national" | "city";
  amount: string;
  deadline: string;
  description: string;
  applyLink: string;
  fbPost: string;
  status: "available" | "pending" | "approved";
}

const scholarships: Scholarship[] = [
  {
    id: "dost-sei",
    name: "DOST-SEI RA 7687 Merit Scholarship",
    organization: "Department of Science and Technology",
    location: "Nationwide",
    scope: "national",
    amount: "Full tuition + PHP 7,000/mo stipend",
    deadline: "Applications open every January",
    description: "For graduating HS students enrolling in priority S&T courses. Covers tuition, fees, book allowance, and monthly stipend at state universities.",
    applyLink: "https://www.sei.dost.gov.ph/index.php/programs-and-projects/scholarships/undergraduate-scholarships",
    fbPost: "https://www.facebook.com/DOSTphl/posts/pfbid02JdKpRmQBrZ3v3nWmTqFZvXqKzMwN",
    status: "approved",
  },
  {
    id: "ched-tulong",
    name: "CHED Tulong Dunong Program",
    organization: "Commission on Higher Education",
    location: "Nationwide",
    scope: "national",
    amount: "Up to PHP 60,000/yr",
    deadline: "Check CHED Regional Office",
    description: "Financial assistance for students in HEIs with limited capacity to pay. Priority for students in CHED-identified priority programs.",
    applyLink: "https://chedro4a.ph/index.php/programs/tulong-dunong",
    fbPost: "https://www.facebook.com/CHEDPhilippines/posts/pfbid0r6Y9UhPqwXoX",
    status: "available",
  },
  {
    id: "sm-foundation",
    name: "SM Foundation College Scholarship",
    organization: "SM Foundation Inc.",
    location: "Nationwide",
    scope: "national",
    amount: "Full tuition + monthly allowance",
    deadline: "Applications open every March",
    description: "For academically talented but financially disadvantaged students. Covers tuition, fees, monthly allowance, and book stipend for 4-5 years.",
    applyLink: "https://www.sm-foundation.org/program/sm-college-scholarship-program/",
    fbPost: "https://www.facebook.com/SMFoundationInc/posts/pfbid0bUPdNtwZ7nz",
    status: "available",
  },
  {
    id: "quezon-city",
    name: "QC-OSCA Iskolar ng Bayan",
    organization: "Quezon City Scholarship Office",
    location: "Quezon City",
    scope: "city",
    amount: "PHP 8,000 - 15,000/sem",
    deadline: "June and November yearly",
    description: "For QC residents enrolled in state or private HEIs. Requires 3+ years residency, GWA of 85% or above, and family income below threshold.",
    applyLink: "https://quezoncity.gov.ph/qc-scholarship/",
    fbPost: "https://www.facebook.com/QCGov/posts/pfbid02vR3xMh9VqRkZJw",
    status: "available",
  },
  {
    id: "makati-umc",
    name: "University of Makati Scholarship",
    organization: "City Government of Makati",
    location: "Makati City",
    scope: "city",
    amount: "Full tuition + PHP 5,000/mo",
    deadline: "Enrollment period",
    description: "Complete free education for Makati residents at the University of Makati. Includes tuition, monthly stipend, books, and uniform allowance.",
    applyLink: "https://www.umak.edu.ph/admission",
    fbPost: "https://www.facebook.com/CityOfMakati/posts/pfbid0cN7LqPx2rBh",
    status: "pending",
  },
  {
    id: "pasig-centenaryo",
    name: "Pasig City Centenaryo Scholarship",
    organization: "City Government of Pasig",
    location: "Pasig City",
    scope: "city",
    amount: "PHP 10,000/sem + book allowance",
    deadline: "Every semester opening",
    description: "For bonafide Pasig residents with at least 2 years residency. Covers semestral tuition assistance and book allowance for college students.",
    applyLink: "https://www.pasigcity.gov.ph/scholarship",
    fbPost: "https://www.facebook.com/PasigCityGovernment/posts/pfbid02QbvRz",
    status: "available",
  },
];

export default function BrowseScholarshipsPage() {
  const [activeTab, setActiveTab] = useState<ScholarshipScope>("all");
  const filtered = activeTab === "all" ? scholarships : scholarships.filter(s => s.scope === activeTab);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Scholarships</h1>
        <p className="mt-1 text-[13px] text-gray-400">Browse available programs. Apply externally, receive funds here.</p>
      </div>

      {/* How it works */}
      <div className="rounded-xl border border-black/[0.04] bg-white p-4">
        <p className="text-[11px] font-medium text-gray-400 uppercase tracking-wider mb-2">How it works</p>
        <div className="flex items-start gap-8 text-[11px] text-gray-500">
          <div className="flex items-center gap-1.5"><span className="flex h-4 w-4 items-center justify-center rounded-full bg-gray-100 text-[9px] font-bold text-gray-500">1</span> Browse &amp; apply externally</div>
          <div className="flex items-center gap-1.5"><span className="flex h-4 w-4 items-center justify-center rounded-full bg-gray-100 text-[9px] font-bold text-gray-500">2</span> Provider verifies you</div>
          <div className="flex items-center gap-1.5"><span className="flex h-4 w-4 items-center justify-center rounded-full bg-merit-gold/20 text-[9px] font-bold text-merit-gold">3</span> Receive funds in Merit</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-1 rounded-lg bg-white border border-black/[0.04] p-1 w-fit">
        <TabBtn active={activeTab === "all"} onClick={() => setActiveTab("all")} label="All" count={scholarships.length} />
        <TabBtn active={activeTab === "national"} onClick={() => setActiveTab("national")} label="National" count={scholarships.filter(s => s.scope === "national").length} icon={<Globe className="h-3 w-3" />} />
        <TabBtn active={activeTab === "city"} onClick={() => setActiveTab("city")} label="City-based" count={scholarships.filter(s => s.scope === "city").length} icon={<Building2 className="h-3 w-3" />} />
      </div>

      {/* List */}
      <div className="space-y-3">
        {filtered.map(s => <ScholarshipCard key={s.id} scholarship={s} />)}
      </div>
    </div>
  );
}

function TabBtn({ active, onClick, label, count, icon }: { active: boolean; onClick: () => void; label: string; count: number; icon?: React.ReactNode }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[12px] font-medium transition-all ${active ? "bg-merit-gold/10 text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}>
      {icon}{label}<span className={`text-[10px] ${active ? "text-merit-gold" : "text-gray-400"}`}>{count}</span>
    </button>
  );
}

function ScholarshipCard({ scholarship }: { scholarship: Scholarship }) {
  const s = scholarship;
  return (
    <div className="rounded-xl border border-black/[0.04] bg-white p-4 md:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-[14px] font-semibold text-gray-900">{s.name}</h3>
            <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide ${s.scope === "national" ? "bg-sky-50 text-sky-700 border border-sky-100" : "bg-amber-50 text-amber-700 border border-amber-100"}`}>
              {s.scope}
            </span>
          </div>
          <p className="text-[12px] text-gray-400 mt-0.5">{s.organization}</p>
        </div>
        {s.status === "approved" && (
          <span className="flex items-center gap-1 rounded-md bg-emerald-50 border border-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700 shrink-0">
            <CheckCircle2 className="h-3 w-3" /> Approved
          </span>
        )}
        {s.status === "pending" && (
          <span className="flex items-center gap-1 rounded-md bg-amber-50 border border-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-700 shrink-0">
            <Clock className="h-3 w-3" /> Pending
          </span>
        )}
      </div>

      <p className="mt-2 text-[12px] text-gray-500 leading-relaxed">{s.description}</p>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px] text-gray-400">
        <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{s.location}</span>
        <span className="flex items-center gap-1"><Banknote className="h-3 w-3" />{s.amount}</span>
        <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{s.deadline}</span>
      </div>

      {/* Action buttons */}
      <div className="mt-4 flex items-center gap-2">
        {s.status === "available" && (
          <>
            <a href={s.applyLink} target="_blank" rel="noopener noreferrer"
              className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-gray-900 py-2.5 text-[12px] font-medium text-white hover:bg-gray-800 transition-all">
              Apply on Official Site <ExternalLink className="h-3 w-3" />
            </a>
            <a href={s.fbPost} target="_blank" rel="noopener noreferrer"
              className="flex items-center justify-center gap-1.5 rounded-lg border border-black/[0.06] bg-[#FAFAF9] px-3 py-2.5 text-[12px] font-medium text-gray-600 hover:border-merit-gold/20 transition-all">
              FB Post <ExternalLink className="h-3 w-3" />
            </a>
          </>
        )}
        {s.status === "pending" && (
          <div className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-amber-50 border border-amber-100 py-2.5 text-[12px] font-medium text-amber-700">
            <Clock className="h-3.5 w-3.5" /> Awaiting provider verification
          </div>
        )}
        {s.status === "approved" && (
          <div className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-emerald-50 border border-emerald-100 py-2.5 text-[12px] font-medium text-emerald-700">
            <CheckCircle2 className="h-3.5 w-3.5" /> Funds received in wallet
          </div>
        )}
      </div>
    </div>
  );
}

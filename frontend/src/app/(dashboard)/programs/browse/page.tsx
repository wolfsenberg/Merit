"use client";

import { useState } from "react";
import { MessageCircle, Heart, Share2, MapPin, ExternalLink, Plus, Globe, Building2, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type FeedFilter = "all" | "national" | "city";

interface ScholarshipPost {
  id: string;
  author: string;
  authorInitials: string;
  university: string;
  postedAt: string;
  scholarshipName: string;
  scope: "national" | "city";
  location: string;
  description: string;
  link?: string;
  likes: number;
  comments: number;
  isLiked: boolean;
}

const posts: ScholarshipPost[] = [
  {
    id: "p1",
    author: "Maria S.",
    authorInitials: "MS",
    university: "UP Diliman",
    postedAt: "2h ago",
    scholarshipName: "DOST-SEI RA 7687",
    scope: "national",
    location: "Nationwide",
    description: "Applications for next sem are open na! Deadline is January. GWA requirement is 1.75. Worth it kasi full tuition + 7K monthly stipend. Nag-apply ako last year and got in. AMA sa comments.",
    link: "https://www.sei.dost.gov.ph/index.php/programs-and-projects/scholarships",
    likes: 24,
    comments: 8,
    isLiked: false,
  },
  {
    id: "p2",
    author: "Juan R.",
    authorInitials: "JR",
    university: "PUP Manila",
    postedAt: "5h ago",
    scholarshipName: "SM Foundation College Scholarship",
    scope: "national",
    location: "Nationwide",
    description: "For incoming freshmen and current college students na may 85%+ GWA. Application is usually March-April. They cover full tuition + monthly allowance + books. Strict yung family income requirement tho (below 300K annually).",
    link: "https://www.sm-foundation.org/program/sm-college-scholarship-program/",
    likes: 31,
    comments: 12,
    isLiked: true,
  },
  {
    id: "p3",
    author: "Ana C.",
    authorInitials: "AC",
    university: "PLM",
    postedAt: "1d ago",
    scholarshipName: "QC Iskolar ng Bayan",
    scope: "city",
    location: "Quezon City",
    description: "Para sa mga taga-QC! Every June and November pwede mag-apply. Need 3+ years residency and at least 85% GWA. Around 8K-15K per sem depende sa school mo. Requirements: barangay cert, grade slip, enrollment cert.",
    likes: 18,
    comments: 5,
    isLiked: false,
  },
  {
    id: "p4",
    author: "Carlos G.",
    authorInitials: "CG",
    university: "TUP Manila",
    postedAt: "1d ago",
    scholarshipName: "CHED Tulong Dunong",
    scope: "national",
    location: "Nationwide",
    description: "Up to 60K per year! Check nyo sa CHED Regional Office nyo. Priority yung mga naka-enroll sa CHED priority programs (IT, Engineering, Education, etc). Hindi siya compatible with other govt scholarships tho.",
    link: "https://ched.gov.ph",
    likes: 15,
    comments: 3,
    isLiked: false,
  },
  {
    id: "p5",
    author: "Grace L.",
    authorInitials: "GL",
    university: "UMak",
    postedAt: "2d ago",
    scholarshipName: "Makati City College Grant",
    scope: "city",
    location: "Makati City",
    description: "If taga-Makati ka (5+ yrs resident), libre lahat sa University of Makati — tuition, books, monthly 5K stipend, uniform. Basically no reason not to enroll if pasok ka sa requirements. GWA 2.0 or better needed.",
    likes: 42,
    comments: 15,
    isLiked: true,
  },
  {
    id: "p6",
    author: "Demo U.",
    authorInitials: "DU",
    university: "PUP Manila",
    postedAt: "3d ago",
    scholarshipName: "Pasig Centenaryo Scholarship",
    scope: "city",
    location: "Pasig City",
    description: "Taga-Pasig ba kayo? Check nyo 'to — 10K per sem plus book allowance. Need lang 2 years residency at currently enrolled. GWA 2.5 or better. Application every semester opening.",
    likes: 9,
    comments: 2,
    isLiked: false,
  },
];

export default function ScholarshipFeedPage() {
  const [filter, setFilter] = useState<FeedFilter>("all");
  const [feedPosts, setFeedPosts] = useState(posts);

  const filtered = filter === "all" ? feedPosts : feedPosts.filter(p => p.scope === filter);

  const handleLike = (postId: string) => {
    setFeedPosts(prev => prev.map(p =>
      p.id === postId ? { ...p, isLiked: !p.isLiked, likes: p.isLiked ? p.likes - 1 : p.likes + 1 } : p
    ));
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Scholarship Feed</h1>
        <p className="mt-1 text-[13px] text-gray-400">Scholarships recommended by fellow students</p>
      </div>

      {/* Filters */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-1 rounded-lg bg-white border border-black/[0.04] p-1">
          <FilterBtn active={filter === "all"} onClick={() => setFilter("all")} label="All" />
          <FilterBtn active={filter === "national"} onClick={() => setFilter("national")} label="National" icon={<Globe className="h-3 w-3" />} />
          <FilterBtn active={filter === "city"} onClick={() => setFilter("city")} label="City" icon={<Building2 className="h-3 w-3" />} />
        </div>
        <Button className="h-8 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-[11px] font-medium px-3 flex items-center gap-1.5">
          <Plus className="h-3 w-3" /> Share
        </Button>
      </div>

      {/* Feed */}
      <div className="space-y-3">
        {filtered.map(post => (
          <PostCard key={post.id} post={post} onLike={() => handleLike(post.id)} />
        ))}
      </div>
    </div>
  );
}

function FilterBtn({ active, onClick, label, icon }: { active: boolean; onClick: () => void; label: string; icon?: React.ReactNode }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-1 rounded-md px-2.5 py-1.5 text-[11px] font-medium transition-all ${active ? "bg-merit-gold/10 text-gray-900" : "text-gray-500 hover:text-gray-700"}`}>
      {icon}{label}
    </button>
  );
}

function PostCard({ post, onLike }: { post: ScholarshipPost; onLike: () => void }) {
  return (
    <div className="rounded-xl border border-black/[0.04] bg-white p-4">
      {/* Author */}
      <div className="flex items-center gap-2.5 mb-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#FAFAF9] text-[10px] font-semibold text-gray-500 border border-black/[0.04]">
          {post.authorInitials}
        </div>
        <div className="flex-1">
          <p className="text-[12px] font-medium text-gray-900">{post.author} <span className="text-gray-400 font-normal">from {post.university}</span></p>
          <p className="text-[10px] text-gray-400 flex items-center gap-1"><Clock className="h-2.5 w-2.5" /> {post.postedAt}</p>
        </div>
        <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide ${post.scope === "national" ? "bg-sky-50 text-sky-700 border border-sky-100" : "bg-amber-50 text-amber-700 border border-amber-100"}`}>
          {post.scope}
        </span>
      </div>

      {/* Scholarship name */}
      <h3 className="text-[14px] font-semibold text-gray-900 mb-1">{post.scholarshipName}</h3>
      <div className="flex items-center gap-1.5 text-[10px] text-gray-400 mb-2">
        <MapPin className="h-3 w-3" /> {post.location}
      </div>

      {/* Description */}
      <p className="text-[12px] text-gray-600 leading-relaxed">{post.description}</p>

      {/* Link */}
      {post.link && (
        <a href={post.link} target="_blank" rel="noopener noreferrer" className="mt-2 inline-flex items-center gap-1 text-[11px] font-medium text-merit-gold hover:text-gold-600 transition-colors">
          Official link <ExternalLink className="h-3 w-3" />
        </a>
      )}

      {/* Actions */}
      <div className="mt-3 flex items-center gap-4 pt-3 border-t border-black/[0.03]">
        <button onClick={onLike} className={`flex items-center gap-1.5 text-[11px] font-medium transition-colors ${post.isLiked ? "text-red-500" : "text-gray-400 hover:text-gray-600"}`}>
          <Heart className={`h-3.5 w-3.5 ${post.isLiked ? "fill-current" : ""}`} /> {post.likes}
        </button>
        <button className="flex items-center gap-1.5 text-[11px] font-medium text-gray-400 hover:text-gray-600 transition-colors">
          <MessageCircle className="h-3.5 w-3.5" /> {post.comments}
        </button>
        <button className="flex items-center gap-1.5 text-[11px] font-medium text-gray-400 hover:text-gray-600 transition-colors">
          <Share2 className="h-3.5 w-3.5" /> Share
        </button>
      </div>
    </div>
  );
}

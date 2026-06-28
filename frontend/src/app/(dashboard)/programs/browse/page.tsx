"use client";

import { useState } from "react";
import { MessageCircle, Heart, Share2, ExternalLink, Plus, Clock, Send, ArrowLeft, AlertCircle, CheckCircle2, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useLang } from "@/lib/i18n";

type Tab = "share" | "concerns";
type ConcernView = "programs" | "list" | "new";

// ============================================================
// DATA
// ============================================================

interface Post {
  id: string; author: string; initials: string; university: string; time: string;
  title: string; body: string; link?: string; likes: number; comments: number; liked: boolean;
}

const posts: Post[] = [
  { id: "p1", author: "Maria S.", initials: "MS", university: "UP Diliman", time: "2h ago", title: "DOST-SEI RA 7687", body: "Applications for next sem are open na! Deadline is January. GWA requirement is 1.75. Worth it — full tuition + 7K monthly stipend.", link: "https://www.sei.dost.gov.ph", likes: 24, comments: 8, liked: false },
  { id: "p2", author: "Juan R.", initials: "JR", university: "PUP Manila", time: "5h ago", title: "SM Foundation College Scholarship", body: "For incoming freshmen and current college students na may 85%+ GWA. Application is March-April. Full tuition + monthly allowance + books.", link: "https://www.sm-foundation.org", likes: 31, comments: 12, liked: true },
  { id: "p3", author: "Ana C.", initials: "AC", university: "PLM", time: "1d ago", title: "QC Iskolar ng Bayan", body: "Para sa mga taga-QC! Every June and November pwede mag-apply. Need 3+ years residency at least 85% GWA. Around 8K-15K per sem.", likes: 18, comments: 5, liked: false },
  { id: "p4", author: "Carlos G.", initials: "CG", university: "TUP", time: "2d ago", title: "Makati City College Grant", body: "If taga-Makati ka (5+ yrs resident), libre lahat sa UMak — tuition, books, monthly 5K stipend, uniform.", likes: 42, comments: 15, liked: true },
];

interface ScholarshipProgram {
  id: string; name: string; provider: string; openConcerns: number; totalConcerns: number;
}

const myPrograms: ScholarshipProgram[] = [
  { id: "dost", name: "DOST-SEI Merit Scholarship", provider: "DOST", openConcerns: 1, totalConcerns: 2 },
  { id: "sm", name: "SM Foundation Scholarship", provider: "SM Foundation", openConcerns: 0, totalConcerns: 0 },
];

interface Concern {
  id: string; programId: string; subject: string; body: string;
  status: "open" | "replied" | "resolved"; date: string;
  reply?: string; replyFrom?: string;
}

const allConcerns: Concern[] = [
  { id: "c1", programId: "dost", subject: "Late stipend for June", body: "Hindi pa po dumating yung stipend ko for June. Usually by 15th nandun na pero wala pa rin.", status: "replied", date: "Jun 20", reply: "We apologize for the delay. June stipends will be released by June 28. Please check your Merit wallet.", replyFrom: "DOST-SEI Admin" },
  { id: "c2", programId: "dost", subject: "Change of school next sem", body: "I'm transferring to another university next semester. What documents do I need to submit?", status: "open", date: "Jun 25" },
];

// ============================================================
// MAIN COMPONENT
// ============================================================

export default function ScholarsHubPage() {
  const { text } = useLang();
  const [tab, setTab] = useState<Tab>("share");

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Scholars Hub</h1>
        <p className="mt-1 text-[13px] text-gray-400">Share, discover, and get support</p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 rounded-lg bg-white border border-black/[0.04] p-1">
        <button onClick={() => setTab("share")} className={`flex-1 rounded-md px-3 py-2 text-[12px] font-medium text-center transition-all ${tab === "share" ? "bg-merit-gold/10 text-gray-900 shadow-sm" : "text-gray-500"}`}>
          Share
        </button>
        <button onClick={() => setTab("concerns")} className={`flex-1 rounded-md px-3 py-2 text-[12px] font-medium text-center transition-all ${tab === "concerns" ? "bg-merit-gold/10 text-gray-900 shadow-sm" : "text-gray-500"}`}>
          Concerns
        </button>
      </div>

      {tab === "share" && <ShareTab />}
      {tab === "concerns" && <ConcernsTab />}
    </div>
  );
}

// ============================================================
// SHARE TAB
// ============================================================

function ShareTab() {
  const [feedPosts, setFeedPosts] = useState(posts);
  const [showNewPost, setShowNewPost] = useState(false);
  const [newPostText, setNewPostText] = useState("");

  const handleLike = (id: string) => {
    setFeedPosts(prev => prev.map(p => p.id === id ? { ...p, liked: !p.liked, likes: p.liked ? p.likes - 1 : p.likes + 1 } : p));
  };

  return (
    <div className="space-y-3">
      <div className="rounded-xl border border-black/[0.04] bg-white p-3">
        {showNewPost ? (
          <div className="space-y-2">
            <textarea value={newPostText} onChange={e => setNewPostText(e.target.value)} placeholder="Share a scholarship tip or recommendation..." className="w-full h-20 rounded-lg border border-black/[0.06] bg-[#FAFAF9] px-3 py-2 text-[13px] resize-none focus:outline-none focus:border-merit-gold" />
            <div className="flex justify-end gap-2">
              <Button onClick={() => setShowNewPost(false)} variant="ghost" className="h-8 text-[11px]">Cancel</Button>
              <Button onClick={() => { setShowNewPost(false); setNewPostText(""); }} className="h-8 rounded-lg bg-merit-gold hover:bg-gold-500 text-white text-[11px] px-3">Post</Button>
            </div>
          </div>
        ) : (
          <button onClick={() => setShowNewPost(true)} className="w-full text-left text-[13px] text-gray-400 hover:text-gray-600">
            Share a scholarship you know about...
          </button>
        )}
      </div>

      {feedPosts.map(post => (
        <div key={post.id} className="rounded-xl border border-black/[0.04] bg-white p-4">
          <div className="flex items-center gap-2.5 mb-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#FAFAF9] text-[9px] font-semibold text-gray-500 border border-black/[0.04]">{post.initials}</div>
            <p className="flex-1 text-[11px] font-medium text-gray-900">{post.author} <span className="text-gray-400 font-normal">· {post.university}</span></p>
            <span className="text-[9px] text-gray-400">{post.time}</span>
          </div>
          <h3 className="text-[13px] font-semibold text-gray-900 mb-1">{post.title}</h3>
          <p className="text-[11px] text-gray-600 leading-relaxed">{post.body}</p>
          {post.link && <a href={post.link} target="_blank" rel="noopener noreferrer" className="mt-1.5 inline-flex items-center gap-1 text-[10px] font-medium text-merit-gold">Link <ExternalLink className="h-2.5 w-2.5" /></a>}
          <div className="mt-2.5 flex items-center gap-4 pt-2.5 border-t border-black/[0.03]">
            <button onClick={() => handleLike(post.id)} className={`flex items-center gap-1 text-[10px] font-medium ${post.liked ? "text-red-500" : "text-gray-400"}`}><Heart className={`h-3 w-3 ${post.liked ? "fill-current" : ""}`} /> {post.likes}</button>
            <button className="flex items-center gap-1 text-[10px] font-medium text-gray-400"><MessageCircle className="h-3 w-3" /> {post.comments}</button>
            <button className="flex items-center gap-1 text-[10px] font-medium text-gray-400"><Share2 className="h-3 w-3" /> Share</button>
          </div>
        </div>
      ))}
    </div>
  );
}

// ============================================================
// CONCERNS TAB — with program selection first
// ============================================================

function ConcernsTab() {
  const [view, setView] = useState<ConcernView>("programs");
  const [selectedProgram, setSelectedProgram] = useState<ScholarshipProgram | null>(null);
  const [myConcerns, setMyConcerns] = useState(allConcerns);
  const [newSubject, setNewSubject] = useState("");
  const [newBody, setNewBody] = useState("");

  const handleSelectProgram = (program: ScholarshipProgram) => {
    setSelectedProgram(program);
    setView("list");
  };

  const handleBack = () => {
    if (view === "new") setView("list");
    else { setView("programs"); setSelectedProgram(null); }
  };

  const handleSubmit = () => {
    if (!newSubject || !newBody || !selectedProgram) return;
    const concern: Concern = { id: `c-${Date.now()}`, programId: selectedProgram.id, subject: newSubject, body: newBody, status: "open", date: "Just now" };
    setMyConcerns([concern, ...myConcerns]);
    setNewSubject(""); setNewBody(""); setView("list");
  };

  const filteredConcerns = selectedProgram ? myConcerns.filter(c => c.programId === selectedProgram.id) : [];

  // View: Select which scholarship program
  if (view === "programs") {
    return (
      <div className="space-y-3">
        <p className="text-[12px] text-gray-500">Select which scholarship you need help with:</p>
        {myPrograms.map(program => (
          <button key={program.id} onClick={() => handleSelectProgram(program)} className="w-full rounded-xl border border-black/[0.04] bg-white p-4 text-left transition-all hover:border-merit-gold/20 hover:shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[13px] font-semibold text-gray-900">{program.name}</p>
                <p className="text-[11px] text-gray-400 mt-0.5">{program.provider}</p>
              </div>
              <div className="flex items-center gap-2">
                {program.openConcerns > 0 && (
                  <span className="flex items-center gap-1 rounded-md bg-amber-50 border border-amber-100 px-1.5 py-0.5 text-[9px] font-medium text-amber-700">
                    {program.openConcerns} open
                  </span>
                )}
                <ChevronRight className="h-4 w-4 text-gray-300" />
              </div>
            </div>
          </button>
        ))}
      </div>
    );
  }

  // View: New concern form
  if (view === "new") {
    return (
      <div className="space-y-4">
        <button onClick={handleBack} className="flex items-center gap-1.5 text-[12px] text-gray-400 hover:text-gray-600">
          <ArrowLeft className="h-3.5 w-3.5" /> Back
        </button>
        <div className="rounded-xl border border-black/[0.04] bg-white p-4 space-y-3">
          <div className="flex items-center gap-2 pb-3 border-b border-black/[0.04]">
            <AlertCircle className="h-4 w-4 text-merit-gold" />
            <p className="text-[12px] font-medium text-gray-900">New concern for {selectedProgram?.name}</p>
          </div>
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Subject</label>
            <Input value={newSubject} onChange={e => setNewSubject(e.target.value)} placeholder="e.g., Late payout, Missing stipend" className="h-10 rounded-lg border-black/[0.06] bg-[#FAFAF9] text-[12px]" />
          </div>
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Details</label>
            <textarea value={newBody} onChange={e => setNewBody(e.target.value)} placeholder="Describe your concern..." className="w-full h-24 rounded-lg border border-black/[0.06] bg-[#FAFAF9] px-3 py-2 text-[12px] resize-none focus:outline-none focus:border-merit-gold" />
          </div>
          <Button onClick={handleSubmit} disabled={!newSubject || !newBody} className="w-full h-10 rounded-lg bg-merit-gold hover:bg-gold-500 text-white text-[12px] font-medium flex items-center gap-1.5">
            <Send className="h-3.5 w-3.5" /> Submit Concern
          </Button>
        </div>
      </div>
    );
  }

  // View: Concerns list for selected program
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <button onClick={handleBack} className="flex items-center gap-1.5 text-[12px] text-gray-400 hover:text-gray-600">
          <ArrowLeft className="h-3.5 w-3.5" /> All Programs
        </button>
        <Button onClick={() => setView("new")} className="h-8 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-[11px] font-medium px-3 flex items-center gap-1">
          <Plus className="h-3 w-3" /> New Concern
        </Button>
      </div>

      <div className="rounded-lg bg-merit-gold/[0.04] border border-merit-gold/10 px-3 py-2">
        <p className="text-[12px] font-medium text-gray-900">{selectedProgram?.name}</p>
        <p className="text-[10px] text-gray-400">{selectedProgram?.provider}</p>
      </div>

      {filteredConcerns.length === 0 ? (
        <div className="py-10 text-center">
          <p className="text-[13px] text-gray-400">No concerns yet for this program.</p>
          <Button onClick={() => setView("new")} variant="ghost" className="mt-2 text-[12px] text-merit-gold">Raise your first concern</Button>
        </div>
      ) : (
        filteredConcerns.map(concern => (
          <div key={concern.id} className="rounded-xl border border-black/[0.04] bg-white p-4">
            <div className="flex items-start justify-between gap-2">
              <p className="text-[13px] font-medium text-gray-900">{concern.subject}</p>
              <span className={`flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[9px] font-medium shrink-0 ${
                concern.status === "open" ? "bg-amber-50 text-amber-700 border-amber-100" :
                concern.status === "replied" ? "bg-sky-50 text-sky-700 border-sky-100" :
                "bg-emerald-50 text-emerald-700 border-emerald-100"
              }`}>
                {concern.status === "open" && <><Clock className="h-2.5 w-2.5" /> Open</>}
                {concern.status === "replied" && <><MessageCircle className="h-2.5 w-2.5" /> Replied</>}
                {concern.status === "resolved" && <><CheckCircle2 className="h-2.5 w-2.5" /> Resolved</>}
              </span>
            </div>
            <p className="text-[10px] text-gray-400 mt-1">{concern.date}</p>
            <p className="mt-2 text-[11px] text-gray-600 leading-relaxed">{concern.body}</p>
            {concern.reply && (
              <div className="mt-3 rounded-lg bg-[#FAFAF9] border border-black/[0.04] p-3">
                <p className="text-[10px] font-medium text-gray-500 mb-1">{concern.replyFrom}</p>
                <p className="text-[11px] text-gray-700 leading-relaxed">{concern.reply}</p>
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import { MessageCircle, Heart, Share2, MapPin, ExternalLink, Plus, Globe, Building2, Clock, Send, ChevronDown, AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useLang } from "@/lib/i18n";

type Tab = "share" | "concerns";

// ============================================================
// SHARE TAB DATA
// ============================================================

interface Post {
  id: string;
  author: string;
  initials: string;
  university: string;
  time: string;
  title: string;
  scope: "national" | "city";
  location: string;
  body: string;
  link?: string;
  likes: number;
  comments: number;
  liked: boolean;
}

const posts: Post[] = [
  { id: "p1", author: "Maria S.", initials: "MS", university: "UP Diliman", time: "2h ago", title: "DOST-SEI RA 7687", scope: "national", location: "Nationwide", body: "Applications for next sem are open na! Deadline is January. GWA requirement is 1.75. Worth it kasi full tuition + 7K monthly stipend.", link: "https://www.sei.dost.gov.ph", likes: 24, comments: 8, liked: false },
  { id: "p2", author: "Juan R.", initials: "JR", university: "PUP Manila", time: "5h ago", title: "SM Foundation College Scholarship", scope: "national", location: "Nationwide", body: "For incoming freshmen and current college students na may 85%+ GWA. Application is March-April. Full tuition + monthly allowance + books.", link: "https://www.sm-foundation.org", likes: 31, comments: 12, liked: true },
  { id: "p3", author: "Ana C.", initials: "AC", university: "PLM", time: "1d ago", title: "QC Iskolar ng Bayan", scope: "city", location: "Quezon City", body: "Para sa mga taga-QC! Every June and November pwede mag-apply. Need 3+ years residency and at least 85% GWA. Around 8K-15K per sem.", likes: 18, comments: 5, liked: false },
  { id: "p4", author: "Carlos G.", initials: "CG", university: "TUP", time: "2d ago", title: "Makati City College Grant", scope: "city", location: "Makati", body: "If taga-Makati ka (5+ yrs resident), libre lahat sa UMak — tuition, books, monthly 5K stipend, uniform.", likes: 42, comments: 15, liked: true },
];

// ============================================================
// CONCERNS TAB DATA
// ============================================================

interface Concern {
  id: string;
  scholarship: string;
  subject: string;
  body: string;
  status: "open" | "replied" | "resolved";
  date: string;
  reply?: string;
  replyFrom?: string;
}

const myScholarships = ["DOST-SEI Merit Scholarship", "SM Foundation Scholarship"];

const concerns: Concern[] = [
  { id: "c1", scholarship: "DOST-SEI Merit Scholarship", subject: "Late stipend for June", body: "Hindi pa po dumating yung stipend ko for June. Usually by 15th nandun na pero wala pa rin.", status: "replied", date: "Jun 20, 2026", reply: "We apologize for the delay. June stipends will be released by June 28. Please check your Merit wallet.", replyFrom: "DOST-SEI Admin" },
  { id: "c2", scholarship: "DOST-SEI Merit Scholarship", subject: "Change of school next sem", body: "I'm transferring to another university next semester. What documents do I need to submit for the transfer?", status: "open", date: "Jun 25, 2026" },
];

// ============================================================
// COMPONENT
// ============================================================

export default function ScholarsHubPage() {
  const { text } = useLang();
  const [tab, setTab] = useState<Tab>("share");
  const [feedPosts, setFeedPosts] = useState(posts);
  const [showNewPost, setShowNewPost] = useState(false);
  const [showNewConcern, setShowNewConcern] = useState(false);
  const [newPostText, setNewPostText] = useState("");
  const [concernScholarship, setConcernScholarship] = useState(myScholarships[0]);
  const [concernSubject, setConcernSubject] = useState("");
  const [concernBody, setConcernBody] = useState("");
  const [myConcerns, setMyConcerns] = useState(concerns);

  const handleLike = (id: string) => {
    setFeedPosts(prev => prev.map(p => p.id === id ? { ...p, liked: !p.liked, likes: p.liked ? p.likes - 1 : p.likes + 1 } : p));
  };

  const handleSubmitConcern = () => {
    if (!concernSubject || !concernBody) return;
    const newConcern: Concern = {
      id: `c-${Date.now()}`,
      scholarship: concernScholarship,
      subject: concernSubject,
      body: concernBody,
      status: "open",
      date: "Just now",
    };
    setMyConcerns([newConcern, ...myConcerns]);
    setConcernSubject("");
    setConcernBody("");
    setShowNewConcern(false);
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Scholars Hub</h1>
        <p className="mt-1 text-[13px] text-gray-400">Community sharing and support</p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 rounded-lg bg-white border border-black/[0.04] p-1">
        <button onClick={() => setTab("share")} className={`flex-1 rounded-md px-3 py-2 text-[12px] font-medium text-center transition-all ${tab === "share" ? "bg-merit-gold/10 text-gray-900 shadow-sm" : "text-gray-500"}`}>
          Share Scholarships
        </button>
        <button onClick={() => setTab("concerns")} className={`flex-1 rounded-md px-3 py-2 text-[12px] font-medium text-center transition-all ${tab === "concerns" ? "bg-merit-gold/10 text-gray-900 shadow-sm" : "text-gray-500"}`}>
          My Concerns
        </button>
      </div>

      {/* SHARE TAB */}
      {tab === "share" && (
        <div className="space-y-3">
          {/* New post input */}
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
              <button onClick={() => setShowNewPost(true)} className="w-full text-left text-[13px] text-gray-400 hover:text-gray-600 transition-colors">
                Share a scholarship you know about...
              </button>
            )}
          </div>

          {/* Feed */}
          {feedPosts.map(post => (
            <div key={post.id} className="rounded-xl border border-black/[0.04] bg-white p-4">
              <div className="flex items-center gap-2.5 mb-2.5">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#FAFAF9] text-[9px] font-semibold text-gray-500 border border-black/[0.04]">{post.initials}</div>
                <div className="flex-1">
                  <p className="text-[11px] font-medium text-gray-900">{post.author} <span className="text-gray-400 font-normal">· {post.university}</span></p>
                </div>
                <span className="text-[9px] text-gray-400">{post.time}</span>
              </div>
              <h3 className="text-[13px] font-semibold text-gray-900 mb-1">{post.title}</h3>
              <p className="text-[11px] text-gray-600 leading-relaxed">{post.body}</p>
              {post.link && (
                <a href={post.link} target="_blank" rel="noopener noreferrer" className="mt-1.5 inline-flex items-center gap-1 text-[10px] font-medium text-merit-gold">
                  Official link <ExternalLink className="h-2.5 w-2.5" />
                </a>
              )}
              <div className="mt-2.5 flex items-center gap-4 pt-2.5 border-t border-black/[0.03]">
                <button onClick={() => handleLike(post.id)} className={`flex items-center gap-1 text-[10px] font-medium ${post.liked ? "text-red-500" : "text-gray-400"}`}>
                  <Heart className={`h-3 w-3 ${post.liked ? "fill-current" : ""}`} /> {post.likes}
                </button>
                <button className="flex items-center gap-1 text-[10px] font-medium text-gray-400"><MessageCircle className="h-3 w-3" /> {post.comments}</button>
                <button className="flex items-center gap-1 text-[10px] font-medium text-gray-400"><Share2 className="h-3 w-3" /> Share</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CONCERNS TAB */}
      {tab === "concerns" && (
        <div className="space-y-3">
          {/* New concern button */}
          <Button onClick={() => setShowNewConcern(!showNewConcern)} className="w-full h-10 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-[12px] font-medium flex items-center gap-1.5">
            <Plus className="h-3.5 w-3.5" /> Raise a Concern
          </Button>

          {/* New concern form */}
          {showNewConcern && (
            <div className="rounded-xl border border-black/[0.04] bg-white p-4 space-y-3 animate-in">
              <div className="space-y-1.5">
                <label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Scholarship Program</label>
                <div className="relative">
                  <select value={concernScholarship} onChange={e => setConcernScholarship(e.target.value)} className="w-full h-10 rounded-lg border border-black/[0.06] bg-[#FAFAF9] px-3 text-[12px] appearance-none focus:outline-none focus:border-merit-gold">
                    {myScholarships.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400 pointer-events-none" />
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Subject</label>
                <Input value={concernSubject} onChange={e => setConcernSubject(e.target.value)} placeholder="e.g., Late stipend, Missing payout" className="h-10 rounded-lg border-black/[0.06] bg-[#FAFAF9] text-[12px]" />
              </div>
              <div className="space-y-1.5">
                <label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Details</label>
                <textarea value={concernBody} onChange={e => setConcernBody(e.target.value)} placeholder="Describe your concern in detail..." className="w-full h-20 rounded-lg border border-black/[0.06] bg-[#FAFAF9] px-3 py-2 text-[12px] resize-none focus:outline-none focus:border-merit-gold" />
              </div>
              <div className="flex gap-2">
                <Button onClick={() => setShowNewConcern(false)} variant="ghost" className="flex-1 h-9 text-[11px]">Cancel</Button>
                <Button onClick={handleSubmitConcern} disabled={!concernSubject || !concernBody} className="flex-1 h-9 rounded-lg bg-merit-gold hover:bg-gold-500 text-white text-[11px] font-medium flex items-center gap-1">
                  <Send className="h-3 w-3" /> Submit
                </Button>
              </div>
            </div>
          )}

          {/* Concerns list */}
          {myConcerns.map(concern => (
            <div key={concern.id} className="rounded-xl border border-black/[0.04] bg-white p-4">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-[13px] font-medium text-gray-900">{concern.subject}</p>
                  <p className="text-[10px] text-gray-400 mt-0.5">{concern.scholarship} · {concern.date}</p>
                </div>
                <span className={`flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[9px] font-medium ${
                  concern.status === "open" ? "bg-amber-50 text-amber-700 border-amber-100" :
                  concern.status === "replied" ? "bg-sky-50 text-sky-700 border-sky-100" :
                  "bg-emerald-50 text-emerald-700 border-emerald-100"
                }`}>
                  {concern.status === "open" && <><Clock className="h-2.5 w-2.5" /> Open</>}
                  {concern.status === "replied" && <><MessageCircle className="h-2.5 w-2.5" /> Replied</>}
                  {concern.status === "resolved" && <><CheckCircle2 className="h-2.5 w-2.5" /> Resolved</>}
                </span>
              </div>
              <p className="mt-2 text-[11px] text-gray-600 leading-relaxed">{concern.body}</p>
              {concern.reply && (
                <div className="mt-3 rounded-lg bg-[#FAFAF9] border border-black/[0.04] p-3">
                  <p className="text-[10px] font-medium text-gray-500 mb-1">{concern.replyFrom}</p>
                  <p className="text-[11px] text-gray-700 leading-relaxed">{concern.reply}</p>
                </div>
              )}
            </div>
          ))}

          {myConcerns.length === 0 && (
            <div className="py-8 text-center text-[13px] text-gray-400">No concerns raised yet.</div>
          )}
        </div>
      )}
    </div>
  );
}

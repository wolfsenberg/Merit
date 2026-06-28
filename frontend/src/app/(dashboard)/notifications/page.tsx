"use client";

import { CheckCircle2, Banknote, FileText, Clock } from "lucide-react";

interface Notification {
  id: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  time: string;
  read: boolean;
}

const notifications: Notification[] = [
  { id: "1", icon: <Banknote className="h-4 w-4 text-merit-gold" />, title: "Funds Disbursed", description: "PHP 10,000 has been sent to your Stellar wallet from DOST-SEI Fund.", time: "2 days ago", read: false },
  { id: "2", icon: <CheckCircle2 className="h-4 w-4 text-emerald-500" />, title: "Documents Verified", description: "All 3 documents for DOST-SEI scholarship have been verified successfully.", time: "3 days ago", read: false },
  { id: "3", icon: <CheckCircle2 className="h-4 w-4 text-emerald-500" />, title: "Eligibility Confirmed", description: "You are now eligible for the DOST-SEI Merit Scholarship.", time: "4 days ago", read: true },
  { id: "4", icon: <FileText className="h-4 w-4 text-sky-400" />, title: "Application Received", description: "Your application to DOST-SEI Merit Scholarship has been received.", time: "1 week ago", read: true },
  { id: "5", icon: <Clock className="h-4 w-4 text-gray-400" />, title: "Verification Started", description: "AI verification has started processing your uploaded documents.", time: "1 week ago", read: true },
];

export default function NotificationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Notifications</h1>
        <p className="mt-1 text-[13px] text-gray-400">{notifications.filter(n => !n.read).length} unread</p>
      </div>

      <div className="rounded-xl border border-black/[0.04] bg-white overflow-hidden">
        {notifications.map((notif, idx) => (
          <div key={notif.id} className={`flex items-start gap-3 p-4 transition-colors ${!notif.read ? "bg-merit-gold/[0.02]" : ""} ${idx < notifications.length - 1 ? "border-b border-black/[0.03]" : ""}`}>
            <div className="mt-0.5 shrink-0">{notif.icon}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className={`text-[13px] font-medium ${!notif.read ? "text-gray-900" : "text-gray-700"}`}>{notif.title}</p>
                {!notif.read && <span className="h-1.5 w-1.5 rounded-full bg-merit-gold" />}
              </div>
              <p className="text-[12px] text-gray-500 mt-0.5 leading-relaxed">{notif.description}</p>
            </div>
            <span className="text-[10px] text-gray-400 whitespace-nowrap shrink-0">{notif.time}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

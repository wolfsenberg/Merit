"use client";

import { useState } from "react";
import { ArrowDownLeft, ArrowUpRight, FileText, CheckCircle2, Clock, Banknote, Filter, ExternalLink } from "lucide-react";

type TxType = "all" | "application" | "disbursement" | "withdrawal";

interface Transaction {
  id: string;
  type: "application_submitted" | "application_accepted" | "documents_verified" | "funds_disbursed" | "funds_withdrawn";
  title: string;
  description: string;
  amount?: string;
  date: string;
  status: "completed" | "pending" | "processing";
  txHash?: string;
  scholarship?: string;
}

const transactions: Transaction[] = [
  {
    id: "tx-7",
    type: "funds_withdrawn",
    title: "Cash Out to GCash",
    description: "Withdrawn from Stellar wallet to GCash account",
    amount: "- PHP 5,000",
    date: "Jun 27, 2026 — 2:15 PM",
    status: "completed",
    txHash: "a3f8c1d2e5...7b9k4m2n",
    scholarship: "DOST-SEI Merit Scholarship",
  },
  {
    id: "tx-6",
    type: "funds_disbursed",
    title: "Scholarship Fund Received",
    description: "DOST-SEI Merit Scholarship — 1st Semester disbursement",
    amount: "+ PHP 10,000",
    date: "Jun 25, 2026 — 10:00 AM",
    status: "completed",
    txHash: "d46785c4b9...588c0c82a3",
    scholarship: "DOST-SEI Merit Scholarship",
  },
  {
    id: "tx-5",
    type: "documents_verified",
    title: "Documents Verified",
    description: "All submitted documents passed AI verification (94% confidence)",
    date: "Jun 23, 2026 — 3:42 PM",
    status: "completed",
    scholarship: "DOST-SEI Merit Scholarship",
  },
  {
    id: "tx-4",
    type: "application_accepted",
    title: "Application Accepted",
    description: "Your scholarship application has been approved",
    date: "Jun 22, 2026 — 9:10 AM",
    status: "completed",
    scholarship: "DOST-SEI Merit Scholarship",
  },
  {
    id: "tx-3",
    type: "application_submitted",
    title: "Application Submitted",
    description: "Submitted application with 3 documents for verification",
    date: "Jun 20, 2026 — 11:30 AM",
    status: "completed",
    scholarship: "DOST-SEI Merit Scholarship",
  },
  {
    id: "tx-2",
    type: "application_submitted",
    title: "Application Submitted",
    description: "Submitted application to SM Foundation Scholarship",
    date: "Jun 18, 2026 — 4:05 PM",
    status: "pending",
    scholarship: "SM Foundation Scholarship",
  },
  {
    id: "tx-1",
    type: "funds_disbursed",
    title: "Wallet Funded",
    description: "Initial testnet funding for wallet activation",
    amount: "+ 100 XLM",
    date: "Jun 15, 2026 — 8:00 AM",
    status: "completed",
    txHash: "5e9715d7dd...54ec262f",
  },
];

const typeFilter: Record<TxType, string> = {
  all: "All",
  application: "Applications",
  disbursement: "Disbursements",
  withdrawal: "Withdrawals",
};

export default function TransactionsPage() {
  const [activeFilter, setActiveFilter] = useState<TxType>("all");

  const filtered = activeFilter === "all" ? transactions : transactions.filter(tx => {
    if (activeFilter === "application") return tx.type === "application_submitted" || tx.type === "application_accepted";
    if (activeFilter === "disbursement") return tx.type === "funds_disbursed" || tx.type === "documents_verified";
    if (activeFilter === "withdrawal") return tx.type === "funds_withdrawn";
    return true;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Transactions</h1>
        <p className="mt-1 text-[13px] text-gray-400">Complete history of your scholarship activity</p>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1 rounded-lg bg-white border border-black/[0.04] p-1 w-fit overflow-x-auto">
        {(Object.keys(typeFilter) as TxType[]).map((key) => (
          <button key={key} onClick={() => setActiveFilter(key)}
            className={`rounded-md px-3 py-1.5 text-[12px] font-medium whitespace-nowrap transition-all ${
              activeFilter === key ? "bg-merit-gold/10 text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
            }`}>
            {typeFilter[key]}
          </button>
        ))}
      </div>

      {/* Transaction list */}
      <div className="rounded-xl border border-black/[0.04] bg-white overflow-hidden">
        {filtered.map((tx, idx) => (
          <TransactionRow key={tx.id} tx={tx} isLast={idx === filtered.length - 1} />
        ))}
        {filtered.length === 0 && (
          <div className="py-12 text-center text-[13px] text-gray-400">No transactions in this category.</div>
        )}
      </div>
    </div>
  );
}

function TransactionRow({ tx, isLast }: { tx: Transaction; isLast: boolean }) {
  const iconMap = {
    application_submitted: <FileText className="h-4 w-4 text-sky-500" strokeWidth={1.8} />,
    application_accepted: <CheckCircle2 className="h-4 w-4 text-emerald-500" strokeWidth={1.8} />,
    documents_verified: <CheckCircle2 className="h-4 w-4 text-emerald-500" strokeWidth={1.8} />,
    funds_disbursed: <ArrowDownLeft className="h-4 w-4 text-emerald-600" strokeWidth={1.8} />,
    funds_withdrawn: <ArrowUpRight className="h-4 w-4 text-orange-500" strokeWidth={1.8} />,
  };

  const statusStyles = {
    completed: "bg-emerald-50 text-emerald-700 border-emerald-100",
    pending: "bg-amber-50 text-amber-700 border-amber-100",
    processing: "bg-sky-50 text-sky-700 border-sky-100",
  };

  return (
    <div className={`flex items-center gap-3 p-4 ${!isLast ? "border-b border-black/[0.03]" : ""}`}>
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#FAFAF9] shrink-0">
        {iconMap[tx.type]}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-[13px] font-medium text-gray-900">{tx.title}</p>
          <span className={`rounded border px-1.5 py-0.5 text-[9px] font-medium ${statusStyles[tx.status]}`}>{tx.status}</span>
        </div>
        <p className="text-[11px] text-gray-400 mt-0.5 truncate">{tx.description}</p>
        <div className="flex items-center gap-3 mt-1">
          <span className="text-[10px] text-gray-400">{tx.date}</span>
          {tx.txHash && (
            <span className="flex items-center gap-0.5 text-[10px] text-gray-400 font-mono">
              <ExternalLink className="h-2.5 w-2.5" /> {tx.txHash}
            </span>
          )}
        </div>
      </div>
      {tx.amount && (
        <p className={`text-[13px] font-semibold shrink-0 ${tx.amount.startsWith("+") ? "text-emerald-600" : "text-orange-600"}`}>
          {tx.amount}
        </p>
      )}
    </div>
  );
}

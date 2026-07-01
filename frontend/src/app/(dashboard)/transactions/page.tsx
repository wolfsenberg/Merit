"use client";

import { useState } from "react";
import { ArrowDownLeft, ArrowUpRight, FileText, CheckCircle2, ExternalLink } from "lucide-react";
import { useDemoLedger } from "@/lib/demo-ledger";

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

const activityTransactions: Transaction[] = [
  {
    id: "tx-5",
    type: "documents_verified",
    title: "Documents Verified",
    description: "All submitted documents passed AI verification (94% confidence)",
    date: "Jun 23, 2026, 3:42 PM",
    status: "completed",
    scholarship: "DOST-SEI Merit Scholarship",
  },
  {
    id: "tx-4",
    type: "application_accepted",
    title: "Application Accepted",
    description: "Your scholarship application has been approved",
    date: "Jun 22, 2026, 9:10 AM",
    status: "completed",
    scholarship: "DOST-SEI Merit Scholarship",
  },
  {
    id: "tx-3",
    type: "application_submitted",
    title: "Application Submitted",
    description: "Submitted application with 3 documents for verification",
    date: "Jun 20, 2026, 11:30 AM",
    status: "completed",
    scholarship: "DOST-SEI Merit Scholarship",
  },
  {
    id: "tx-2",
    type: "application_submitted",
    title: "Application Submitted",
    description: "Submitted application to SM Foundation Scholarship",
    date: "Jun 18, 2026, 4:05 PM",
    status: "pending",
    scholarship: "SM Foundation Scholarship",
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
  const { ledger } = useDemoLedger();

  const moneyTransactions: Transaction[] = ledger.transactions.map((tx) => ({
    id: tx.id,
    type: tx.type,
    title: tx.title,
    description: tx.description,
    amount: `${tx.amount >= 0 ? "+" : "-"} PHP ${Math.abs(tx.amount).toLocaleString()}`,
    date: tx.date,
    status: tx.status,
    txHash: tx.txHash,
    scholarship: tx.scholarship,
  }));
  const transactions = [...moneyTransactions, ...activityTransactions];

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
              <ExternalLink className="h-2.5 w-2.5" /> {tx.txHash.slice(0, 16)}...
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

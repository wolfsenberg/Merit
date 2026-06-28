"use client";

import { getCachedPublicKey } from "@/lib/freighter";
import { Wallet, ArrowDownLeft, ExternalLink, Copy, CheckCircle2 } from "lucide-react";
import { useState } from "react";

interface Transaction {
  id: string;
  type: "received";
  amount: string;
  from: string;
  date: string;
  status: "confirmed";
  hash: string;
}

const mockTransactions: Transaction[] = [
  { id: "1", type: "received", amount: "10,000 XLM", from: "DOST-SEI Scholarship Fund", date: "Jun 25, 2026", status: "confirmed", hash: "d46785c4b9c4...588c0c82a3" },
];

export default function WalletPage() {
  const publicKey = getCachedPublicKey();
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (publicKey) {
      navigator.clipboard.writeText(publicKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Wallet</h1>
        <p className="mt-1 text-[13px] text-gray-400">Your Stellar wallet on testnet</p>
      </div>

      {/* Balance card */}
      <div className="rounded-xl border border-black/[0.04] bg-white p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-merit-gold/10">
            <Wallet className="h-5 w-5 text-merit-gold" strokeWidth={1.5} />
          </div>
          <div>
            <p className="text-[11px] text-gray-400 uppercase tracking-wide">Balance</p>
            <p className="text-[24px] font-semibold tracking-tight text-gray-900">10,000 <span className="text-[14px] text-gray-400 font-normal">XLM</span></p>
          </div>
        </div>

        {publicKey && (
          <div className="flex items-center gap-2 rounded-lg bg-[#FAFAF9] border border-black/[0.04] px-3 py-2.5">
            <p className="flex-1 text-[11px] font-mono text-gray-500 truncate">{publicKey}</p>
            <button onClick={handleCopy} className="flex h-6 w-6 items-center justify-center rounded text-gray-400 hover:text-gray-600 transition-colors">
              {copied ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
            </button>
          </div>
        )}
      </div>

      {/* Transactions */}
      <div>
        <h2 className="text-[13px] font-medium text-gray-400 uppercase tracking-wider mb-3">Transactions</h2>
        <div className="rounded-xl border border-black/[0.04] bg-white overflow-hidden">
          {mockTransactions.map((tx, idx) => (
            <div key={tx.id} className={`flex items-center gap-3 p-4 ${idx < mockTransactions.length - 1 ? "border-b border-black/[0.03]" : ""}`}>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50">
                <ArrowDownLeft className="h-4 w-4 text-emerald-600" strokeWidth={1.8} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[13px] font-medium text-gray-900">{tx.from}</p>
                <p className="text-[11px] text-gray-400">{tx.date}</p>
              </div>
              <div className="text-right">
                <p className="text-[13px] font-semibold text-emerald-600">+{tx.amount}</p>
                <p className="text-[10px] text-gray-400 font-mono">{tx.hash}</p>
              </div>
            </div>
          ))}
          {mockTransactions.length === 0 && (
            <div className="p-8 text-center text-[13px] text-gray-400">No transactions yet</div>
          )}
        </div>
      </div>

      {/* Explorer link */}
      <a href="https://stellar.expert/explorer/testnet" target="_blank" rel="noopener noreferrer"
        className="flex items-center justify-center gap-1.5 text-[12px] font-medium text-gray-400 hover:text-merit-gold transition-colors">
        View on Stellar Explorer <ExternalLink className="h-3 w-3" />
      </a>
    </div>
  );
}

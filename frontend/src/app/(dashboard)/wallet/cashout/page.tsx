"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Smartphone, Building2, CheckCircle2, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type CashOutMethod = "gcash" | "maya" | "bank" | null;
type Step = "method" | "details" | "confirm" | "success";

export default function CashOutPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("method");
  const [method, setMethod] = useState<CashOutMethod>(null);
  const [amount, setAmount] = useState("");
  const [accountNumber, setAccountNumber] = useState("");
  const [accountName, setAccountName] = useState("");

  const balance = 10000;
  const parsedAmount = parseFloat(amount) || 0;

  const handleSubmit = () => {
    setStep("success");
  };

  return (
    <div className="space-y-6">
      <button onClick={() => router.push("/dashboard")} className="flex items-center gap-1.5 text-[13px] text-gray-400 hover:text-gray-600 transition-colors">
        <ArrowLeft className="h-3.5 w-3.5" /> Back
      </button>

      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Cash Out</h1>
        <p className="mt-1 text-[13px] text-gray-400">Transfer funds to your account — zero fees</p>
      </div>

      {/* Zero fee badge */}
      <div className="flex items-center gap-2 rounded-lg bg-emerald-50 border border-emerald-100 px-3 py-2">
        <Shield className="h-4 w-4 text-emerald-600" strokeWidth={1.5} />
        <p className="text-[12px] text-emerald-700">No transaction fees. Your full scholarship amount goes to you.</p>
      </div>

      {/* Step 1: Choose method */}
      {step === "method" && (
        <div className="space-y-3">
          <p className="text-[12px] font-medium text-gray-400 uppercase tracking-wider">Select cash out method</p>
          <div className="space-y-2">
            <MethodCard selected={method === "gcash"} onClick={() => setMethod("gcash")} icon={<Smartphone className="h-5 w-5" />} name="GCash" desc="Instant transfer to GCash wallet" />
            <MethodCard selected={method === "maya"} onClick={() => setMethod("maya")} icon={<Smartphone className="h-5 w-5" />} name="Maya" desc="Instant transfer to Maya wallet" />
            <MethodCard selected={method === "bank"} onClick={() => setMethod("bank")} icon={<Building2 className="h-5 w-5" />} name="Bank Transfer" desc="BDO, BPI, Unionbank, etc. (1-2 business days)" />
          </div>
          <Button onClick={() => setStep("details")} disabled={!method} className="w-full h-10 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-[13px] font-medium mt-2">
            Continue
          </Button>
        </div>
      )}

      {/* Step 2: Enter details */}
      {step === "details" && (
        <div className="rounded-xl border border-black/[0.04] bg-white p-5 space-y-4">
          <div className="space-y-1.5">
            <Label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Amount (PHP)</Label>
            <Input type="number" value={amount} onChange={e => setAmount(e.target.value)} placeholder="0.00" className="h-12 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[20px] font-semibold text-center" />
            <p className="text-[11px] text-gray-400 text-center">Available: PHP {balance.toLocaleString()}</p>
            <div className="flex gap-2 justify-center mt-2">
              {[1000, 3000, 5000, 10000].map(preset => (
                <button key={preset} onClick={() => setAmount(String(preset))} className={`rounded-md border px-3 py-1 text-[11px] font-medium transition-all ${amount === String(preset) ? "border-merit-gold bg-merit-gold/10 text-gray-900" : "border-black/[0.06] text-gray-500"}`}>
                  {preset >= 1000 ? `${preset / 1000}K` : preset}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">
              {method === "bank" ? "Account Number" : `${method === "gcash" ? "GCash" : "Maya"} Number`}
            </Label>
            <Input value={accountNumber} onChange={e => setAccountNumber(e.target.value)} placeholder={method === "bank" ? "1234567890" : "09XX XXX XXXX"} className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[13px]" />
          </div>

          <div className="space-y-1.5">
            <Label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Account Name</Label>
            <Input value={accountName} onChange={e => setAccountName(e.target.value)} placeholder="Juan Dela Cruz" className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[13px]" />
          </div>

          <div className="flex gap-2">
            <Button onClick={() => setStep("method")} variant="ghost" className="flex-1 h-10 rounded-lg text-[12px]">Back</Button>
            <Button onClick={() => setStep("confirm")} disabled={!amount || parsedAmount <= 0 || parsedAmount > balance || !accountNumber || !accountName} className="flex-1 h-10 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-[13px] font-medium">
              Review
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Confirm */}
      {step === "confirm" && (
        <div className="rounded-xl border border-black/[0.04] bg-white p-5 space-y-4">
          <h3 className="text-[13px] font-medium text-gray-900">Confirm Cash Out</h3>
          <div className="space-y-2 text-[12px]">
            <div className="flex justify-between py-1.5 border-b border-black/[0.03]">
              <span className="text-gray-400">Method</span>
              <span className="font-medium text-gray-900 capitalize">{method}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-black/[0.03]">
              <span className="text-gray-400">Account</span>
              <span className="font-medium text-gray-900">{accountNumber}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-black/[0.03]">
              <span className="text-gray-400">Name</span>
              <span className="font-medium text-gray-900">{accountName}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-black/[0.03]">
              <span className="text-gray-400">Amount</span>
              <span className="font-semibold text-gray-900">PHP {parsedAmount.toLocaleString()}</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-gray-400">Fee</span>
              <span className="font-medium text-emerald-600">FREE</span>
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setStep("details")} variant="ghost" className="flex-1 h-10 rounded-lg text-[12px]">Back</Button>
            <Button onClick={handleSubmit} className="flex-1 h-10 rounded-lg bg-merit-gold hover:bg-gold-500 text-white text-[13px] font-medium shadow-sm shadow-merit-gold/20">
              Confirm Transfer
            </Button>
          </div>
        </div>
      )}

      {/* Step 4: Success */}
      {step === "success" && (
        <div className="rounded-xl border border-black/[0.04] bg-white p-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-50 border border-emerald-100">
            <CheckCircle2 className="h-6 w-6 text-emerald-500" />
          </div>
          <h2 className="text-[18px] font-semibold text-gray-900">Transfer Initiated</h2>
          <p className="mt-2 text-[13px] text-gray-500">
            PHP {parsedAmount.toLocaleString()} is being sent to your {method === "bank" ? "bank account" : `${method} wallet`}.
          </p>
          <p className="mt-1 text-[11px] text-gray-400">
            {method === "bank" ? "Expect 1-2 business days" : "Should arrive within minutes"}
          </p>
          <Button onClick={() => router.push("/dashboard")} className="mt-6 h-10 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-[13px] font-medium px-6">
            Back to Home
          </Button>
        </div>
      )}
    </div>
  );
}

function MethodCard({ selected, onClick, icon, name, desc }: { selected: boolean; onClick: () => void; icon: React.ReactNode; name: string; desc: string }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-3 w-full rounded-xl border-2 p-4 text-left transition-all ${selected ? "border-merit-gold bg-merit-gold/[0.03]" : "border-black/[0.04] hover:border-black/[0.08]"}`}>
      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${selected ? "bg-merit-gold/10 text-merit-gold" : "bg-[#FAFAF9] text-gray-400"}`}>
        {icon}
      </div>
      <div>
        <p className={`text-[13px] font-medium ${selected ? "text-gray-900" : "text-gray-700"}`}>{name}</p>
        <p className="text-[11px] text-gray-400">{desc}</p>
      </div>
    </button>
  );
}

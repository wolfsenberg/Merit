"use client";

import { useState } from "react";
import { PiggyBank, Plus, Lock, CheckCircle2, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface SavingsGoal {
  id: string;
  name: string;
  target: number;
  saved: number;
  locked: boolean;
  createdAt: string;
}

const mockGoals: SavingsGoal[] = [
  { id: "1", name: "Laptop Fund", target: 10000, saved: 3500, locked: true, createdAt: "Jun 2026" },
  { id: "2", name: "Emergency Fund", target: 5000, saved: 5000, locked: false, createdAt: "May 2026" },
  { id: "3", name: "Books Next Sem", target: 3000, saved: 800, locked: true, createdAt: "Jun 2026" },
];

const presetAmounts = [5000, 10000, 15000, 20000];

export default function SavingsPage() {
  const [goals, setGoals] = useState<SavingsGoal[]>(mockGoals);
  const [showCreate, setShowCreate] = useState(false);
  const [newGoalName, setNewGoalName] = useState("");
  const [newGoalTarget, setNewGoalTarget] = useState("");

  const totalSaved = goals.reduce((sum, g) => sum + g.saved, 0);
  const totalTarget = goals.reduce((sum, g) => sum + g.target, 0);

  const handleCreate = () => {
    if (!newGoalName || !newGoalTarget) return;
    const goal: SavingsGoal = {
      id: `new-${Date.now()}`,
      name: newGoalName,
      target: parseInt(newGoalTarget),
      saved: 0,
      locked: true,
      createdAt: "Jun 2026",
    };
    setGoals([goal, ...goals]);
    setNewGoalName("");
    setNewGoalTarget("");
    setShowCreate(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">Savings Goals</h1>
          <p className="mt-1 text-[13px] text-gray-400">Set it, lock it, reach it.</p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)} className="h-9 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-[12px] font-medium px-3 flex items-center gap-1.5">
          <Plus className="h-3.5 w-3.5" /> New Goal
        </Button>
      </div>

      {/* Summary */}
      <div className="rounded-xl border border-merit-gold/20 bg-merit-gold/[0.03] p-4">
        <div className="flex items-center gap-3">
          <PiggyBank className="h-6 w-6 text-merit-gold" strokeWidth={1.5} />
          <div>
            <p className="text-[11px] text-gray-400 uppercase tracking-wide">Total Saved</p>
            <p className="text-[20px] font-bold text-gray-900">PHP {totalSaved.toLocaleString()} <span className="text-[12px] font-normal text-gray-400">/ {totalTarget.toLocaleString()}</span></p>
          </div>
        </div>
      </div>

      {/* Create goal form */}
      {showCreate && (
        <div className="rounded-xl border border-black/[0.06] bg-white p-5 space-y-4 animate-in">
          <h3 className="text-[13px] font-medium text-gray-900">Create Savings Goal</h3>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">What are you saving for?</Label>
              <Input value={newGoalName} onChange={e => setNewGoalName(e.target.value)} placeholder="e.g., New Phone, Tuition, Emergency" className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[13px]" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">Target Amount (PHP)</Label>
              <Input type="number" value={newGoalTarget} onChange={e => setNewGoalTarget(e.target.value)} placeholder="10000" className="h-10 rounded-lg border-black/[0.08] bg-[#FAFAF9] text-[13px]" />
              <div className="flex gap-2 mt-2">
                {presetAmounts.map(amount => (
                  <button key={amount} onClick={() => setNewGoalTarget(String(amount))} className={`rounded-md border px-2.5 py-1 text-[11px] font-medium transition-all ${newGoalTarget === String(amount) ? "border-merit-gold bg-merit-gold/10 text-gray-900" : "border-black/[0.06] text-gray-500 hover:border-merit-gold/30"}`}>
                    {amount >= 1000 ? `${amount / 1000}K` : amount}
                  </button>
                ))}
              </div>
            </div>
            <div className="rounded-lg bg-[#FAFAF9] border border-black/[0.04] p-3 flex items-start gap-2">
              <Lock className="h-3.5 w-3.5 text-gray-400 mt-0.5 shrink-0" />
              <p className="text-[11px] text-gray-500 leading-relaxed">Funds locked in this goal cannot be withdrawn until the target is reached. This helps you stay on track.</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setShowCreate(false)} variant="ghost" className="flex-1 h-9 rounded-lg text-[12px]">Cancel</Button>
            <Button onClick={handleCreate} disabled={!newGoalName || !newGoalTarget} className="flex-1 h-9 rounded-lg bg-merit-gold hover:bg-gold-500 text-white text-[12px] font-medium">Create Goal</Button>
          </div>
        </div>
      )}

      {/* Goals list */}
      <div className="space-y-3">
        {goals.map(goal => {
          const percent = Math.min(100, Math.round((goal.saved / goal.target) * 100));
          const isComplete = goal.saved >= goal.target;
          return (
            <div key={goal.id} className="rounded-xl border border-black/[0.04] bg-white p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  {isComplete ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-500" strokeWidth={1.8} />
                  ) : (
                    <Target className="h-5 w-5 text-merit-gold" strokeWidth={1.8} />
                  )}
                  <div>
                    <p className="text-[13px] font-medium text-gray-900">{goal.name}</p>
                    <p className="text-[11px] text-gray-400">Started {goal.createdAt}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-[13px] font-semibold text-gray-900">PHP {goal.saved.toLocaleString()}</p>
                  <p className="text-[10px] text-gray-400">of {goal.target.toLocaleString()}</p>
                </div>
              </div>
              <div className="mt-3 h-1.5 rounded-full bg-gray-100 overflow-hidden">
                <div className={`h-full rounded-full transition-all ${isComplete ? "bg-emerald-500" : "bg-merit-gold"}`} style={{ width: `${percent}%` }} />
              </div>
              <div className="mt-2 flex items-center justify-between">
                <span className="text-[10px] text-gray-400">{percent}% reached</span>
                {goal.locked && !isComplete && (
                  <span className="flex items-center gap-1 text-[10px] text-gray-400">
                    <Lock className="h-2.5 w-2.5" /> Locked until target
                  </span>
                )}
                {isComplete && (
                  <span className="text-[10px] font-medium text-emerald-600">Ready to withdraw</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

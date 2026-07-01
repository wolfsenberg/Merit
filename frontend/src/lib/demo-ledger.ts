"use client";

import { useEffect, useState } from "react";
import { getCachedPublicKey } from "@/lib/freighter";

const LEDGER_PREFIX = "merit_demo_ledger";
const ADMIN_STATE_KEY = "merit_demo_admin_disbursements";
const LEDGER_EVENT = "merit-demo-ledger-updated";
const ADMIN_EVENT = "merit-demo-admin-updated";
const DEFAULT_WALLET_KEY = "demo-wallet";

export type DemoTransactionType = "funds_disbursed" | "funds_withdrawn";
export type DemoScholarStatus = "pending" | "approved" | "rejected";

export interface DemoTransaction {
  id: string;
  type: DemoTransactionType;
  title: string;
  description: string;
  amount: number;
  method?: string;
  accountNumber?: string;
  accountName?: string;
  date: string;
  status: "completed" | "processing";
  txHash: string;
  scholarship?: string;
}

export interface DemoLedger {
  walletKey: string;
  balancePhp: number;
  transactions: DemoTransaction[];
  updatedAt: string;
}

export interface DemoScholar {
  id: string;
  name: string;
  email: string;
  studentId: string;
  university: string;
  status: DemoScholarStatus;
  appliedDate: string;
  amount: number;
  disbursedAt?: string;
  txHash?: string;
}

export interface AdminDisbursementRecord {
  id: string;
  scholarId: string;
  scholarName: string;
  scholarEmail: string;
  programName: string;
  amount: number;
  date: string;
  txHash: string;
}

export interface AdminDemoState {
  scholars: DemoScholar[];
  records: AdminDisbursementRecord[];
}

const defaultScholars: DemoScholar[] = [
  { id: "s1", name: "Maria Santos", email: "maria.santos@up.edu.ph", studentId: "2022-04521", university: "UP Diliman", status: "pending", appliedDate: "Jun 15, 2026", amount: 10000 },
  { id: "s2", name: "Juan Reyes", email: "j.reyes@ust.edu.ph", studentId: "2021-89032", university: "UST", status: "pending", appliedDate: "Jun 16, 2026", amount: 10000 },
  { id: "s3", name: "Ana Cruz", email: "ana.cruz@admu.edu.ph", studentId: "2023-12890", university: "Ateneo de Manila", status: "pending", appliedDate: "Jun 17, 2026", amount: 10000 },
  { id: "s4", name: "Carlos Garcia", email: "c.garcia@dlsu.edu.ph", studentId: "2022-56781", university: "De La Salle University", status: "pending", appliedDate: "Jun 18, 2026", amount: 10000 },
  { id: "s5", name: "Demo User", email: "demo@merit.app", studentId: "2023-00001", university: "PUP Manila", status: "approved", appliedDate: "Jun 10, 2026", amount: 10000, disbursedAt: "Jun 25, 2026", txHash: "d46785c4b9c4a588c0c82a3" },
  { id: "s6", name: "Grace Lim", email: "g.lim@tup.edu.ph", studentId: "2022-33445", university: "TUP Manila", status: "approved", appliedDate: "Jun 8, 2026", amount: 10000, disbursedAt: "Jun 25, 2026", txHash: "6f32bd4479c0e91a247a91c" },
];

function nowLabel() {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date());
}

function makeId(prefix: string) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function makeHash(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}${Date.now().toString(36)}`;
}

export function getDemoWalletKey() {
  return getCachedPublicKey() || DEFAULT_WALLET_KEY;
}

function ledgerStorageKey(walletKey = getDemoWalletKey()) {
  return `${LEDGER_PREFIX}:${walletKey}`;
}

function createInitialLedger(walletKey = getDemoWalletKey()): DemoLedger {
  return {
    walletKey,
    balancePhp: 10000,
    updatedAt: new Date().toISOString(),
    transactions: [
      {
        id: "seed_disbursement",
        type: "funds_disbursed",
        title: "Scholarship Fund Received",
        description: "DOST-SEI Merit Scholarship - 1st Semester disbursement",
        amount: 10000,
        date: "Jun 25, 2026, 10:00 AM",
        status: "completed",
        txHash: "d46785c4b9c4a588c0c82a3",
        scholarship: "DOST-SEI Merit Scholarship",
      },
    ],
  };
}

export function readDemoLedger(walletKey = getDemoWalletKey()): DemoLedger {
  if (typeof window === "undefined") return createInitialLedger(walletKey);

  const stored = localStorage.getItem(ledgerStorageKey(walletKey));
  if (!stored) {
    const initial = createInitialLedger(walletKey);
    writeDemoLedger(initial);
    return initial;
  }

  try {
    const parsed = JSON.parse(stored) as DemoLedger;
    return { ...createInitialLedger(walletKey), ...parsed, walletKey };
  } catch {
    const initial = createInitialLedger(walletKey);
    writeDemoLedger(initial);
    return initial;
  }
}

export function writeDemoLedger(ledger: DemoLedger) {
  if (typeof window === "undefined") return;
  const next = { ...ledger, updatedAt: new Date().toISOString() };
  localStorage.setItem(ledgerStorageKey(next.walletKey), JSON.stringify(next));
  window.dispatchEvent(new CustomEvent(LEDGER_EVENT, { detail: next.walletKey }));
}

export function cashOutDemoLedger(input: {
  amount: number;
  method: string;
  accountNumber: string;
  accountName: string;
}) {
  const ledger = readDemoLedger();
  if (input.amount <= 0) throw new Error("Cashout amount must be greater than zero.");
  if (input.amount > ledger.balancePhp) throw new Error("Insufficient available balance.");

  const methodLabel = input.method === "bank" ? "Bank Transfer" : input.method.toUpperCase();
  const transaction: DemoTransaction = {
    id: makeId("cashout"),
    type: "funds_withdrawn",
    title: `Cash Out to ${methodLabel}`,
    description: `Withdrawn from Merit wallet to ${input.accountName}`,
    amount: -input.amount,
    method: input.method,
    accountNumber: input.accountNumber,
    accountName: input.accountName,
    date: nowLabel(),
    status: "completed",
    txHash: makeHash("cashout"),
    scholarship: "DOST-SEI Merit Scholarship",
  };

  const next = {
    ...ledger,
    balancePhp: ledger.balancePhp - input.amount,
    transactions: [transaction, ...ledger.transactions],
  };
  writeDemoLedger(next);
  return next;
}

export function useDemoLedger() {
  const [walletKey, setWalletKey] = useState(DEFAULT_WALLET_KEY);
  const [ledger, setLedger] = useState<DemoLedger>(() => createInitialLedger(DEFAULT_WALLET_KEY));

  useEffect(() => {
    const refresh = () => {
      const nextWalletKey = getDemoWalletKey();
      setWalletKey(nextWalletKey);
      setLedger(readDemoLedger(nextWalletKey));
    };

    refresh();
    window.addEventListener(LEDGER_EVENT, refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener(LEDGER_EVENT, refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);

  return { ledger, walletKey };
}

function createDefaultAdminState(): AdminDemoState {
  return {
    scholars: defaultScholars,
    records: defaultScholars
      .filter((scholar) => scholar.status === "approved")
      .map((scholar) => ({
        id: `seed_${scholar.id}`,
        scholarId: scholar.id,
        scholarName: scholar.name,
        scholarEmail: scholar.email,
        programName: "DOST-SEI Merit Scholarship",
        amount: scholar.amount,
        date: scholar.disbursedAt || "Jun 25, 2026",
        txHash: scholar.txHash || makeHash("disburse"),
      })),
  };
}

export function readAdminDemoState(): AdminDemoState {
  if (typeof window === "undefined") return createDefaultAdminState();

  const stored = localStorage.getItem(ADMIN_STATE_KEY);
  if (!stored) {
    const initial = createDefaultAdminState();
    writeAdminDemoState(initial);
    return initial;
  }

  try {
    return JSON.parse(stored) as AdminDemoState;
  } catch {
    const initial = createDefaultAdminState();
    writeAdminDemoState(initial);
    return initial;
  }
}

export function writeAdminDemoState(state: AdminDemoState) {
  if (typeof window === "undefined") return;
  localStorage.setItem(ADMIN_STATE_KEY, JSON.stringify(state));
  window.dispatchEvent(new CustomEvent(ADMIN_EVENT));
}

export function disburseToScholar(scholarId: string, programName: string) {
  const state = readAdminDemoState();
  const scholar = state.scholars.find((item) => item.id === scholarId);
  if (!scholar || scholar.status !== "pending") return state;

  const txHash = makeHash("disburse");
  const date = nowLabel();
  const updatedScholar: DemoScholar = {
    ...scholar,
    status: "approved",
    disbursedAt: date,
    txHash,
  };
  const record: AdminDisbursementRecord = {
    id: makeId("disbursement"),
    scholarId: scholar.id,
    scholarName: scholar.name,
    scholarEmail: scholar.email,
    programName,
    amount: scholar.amount,
    date,
    txHash,
  };

  const next = {
    scholars: state.scholars.map((item) => (item.id === scholarId ? updatedScholar : item)),
    records: [record, ...state.records],
  };
  writeAdminDemoState(next);
  return next;
}

export function rejectScholarDemo(scholarId: string) {
  const state = readAdminDemoState();
  const next = {
    ...state,
    scholars: state.scholars.map((item) =>
      item.id === scholarId && item.status === "pending"
        ? { ...item, status: "rejected" as const }
        : item
    ),
  };
  writeAdminDemoState(next);
  return next;
}

export function useAdminDemoState() {
  const [state, setState] = useState<AdminDemoState>(() => createDefaultAdminState());

  useEffect(() => {
    const refresh = () => setState(readAdminDemoState());
    refresh();
    window.addEventListener(ADMIN_EVENT, refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener(ADMIN_EVENT, refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);

  return state;
}

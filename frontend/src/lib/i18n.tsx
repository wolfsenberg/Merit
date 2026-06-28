"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";

export type Lang = "en" | "tl";

interface Translations {
  [key: string]: { en: string; tl: string };
}

// All translations — Taglish style for Filipino (not formal Tagalog)
export const t: Translations = {
  // Nav
  "nav.home": { en: "Home", tl: "Home" },
  "nav.feed": { en: "Feed", tl: "Feed" },
  "nav.savings": { en: "Savings", tl: "Ipon" },
  "nav.history": { en: "History", tl: "Talaan" },
  "nav.wallet": { en: "Wallet", tl: "Wallet" },
  "nav.scholarships": { en: "Scholarships", tl: "Scholarships" },
  "nav.documents": { en: "Documents", tl: "Dokumento" },
  "nav.alerts": { en: "Alerts", tl: "Abiso" },

  // Dashboard
  "dash.balance": { en: "Available Balance", tl: "Available na Balance" },
  "dash.receive": { en: "Receive", tl: "Tanggap" },
  "dash.cashout": { en: "Cash Out", tl: "Cash Out" },
  "dash.save": { en: "Save", tl: "Ipon" },
  "dash.active_scholarship": { en: "Active Scholarship", tl: "Active na Scholarship" },
  "dash.recent": { en: "Recent", tl: "Mga Kamakailang Transaksyon" },
  "dash.see_all": { en: "See all", tl: "Tingnan lahat" },
  "dash.scholarship_received": { en: "Scholarship Received", tl: "Na-receive na ang scholarship" },
  "dash.cashout_to": { en: "Cash Out to GCash", tl: "Na-cash out sa GCash" },
  "dash.saved_to": { en: "Saved to", tl: "Na-save sa" },
  "dash.verified": { en: "Verified", tl: "Na-verify na" },
  "dash.next_payout": { en: "Next payout", tl: "Susunod na payout" },
  "dash.amount": { en: "Amount", tl: "Halaga" },

  // Savings
  "savings.title": { en: "Savings Goals", tl: "Savings Goals" },
  "savings.subtitle": { en: "Set it, lock it, reach it.", tl: "I-set, i-lock, abutin." },
  "savings.new_goal": { en: "New Goal", tl: "Bagong Goal" },
  "savings.total_saved": { en: "Total Saved", tl: "Total na Na-save" },
  "savings.create_goal": { en: "Create Savings Goal", tl: "Gawa ng Savings Goal" },
  "savings.what_saving": { en: "What are you saving for?", tl: "Para saan 'to?" },
  "savings.target_amount": { en: "Target Amount (PHP)", tl: "Target Amount (PHP)" },
  "savings.locked_info": { en: "Funds locked in this goal cannot be withdrawn until the target is reached. This helps you stay on track.", tl: "Hindi mo pwede i-withdraw 'to hangga't di mo pa naabot yung target mo. Para disciplined ka." },
  "savings.create": { en: "Create Goal", tl: "Gawa na" },
  "savings.reached": { en: "reached", tl: "na-reach na" },
  "savings.locked": { en: "Locked until target", tl: "Naka-lock hanggang ma-reach" },
  "savings.ready": { en: "Ready to withdraw", tl: "Pwede na i-withdraw" },

  // Cash Out
  "cashout.title": { en: "Cash Out", tl: "Cash Out" },
  "cashout.subtitle": { en: "Transfer funds to your account — zero fees", tl: "I-transfer sa account mo — walang fee" },
  "cashout.no_fee": { en: "No transaction fees. Your full scholarship amount goes to you.", tl: "Walang transaction fee. Buo mong scholarship mapupunta sa'yo." },
  "cashout.select_method": { en: "Select cash out method", tl: "Pumili ng cash out method" },
  "cashout.gcash_desc": { en: "Instant transfer to GCash wallet", tl: "Instant transfer sa GCash" },
  "cashout.maya_desc": { en: "Instant transfer to Maya wallet", tl: "Instant transfer sa Maya" },
  "cashout.bank_desc": { en: "BDO, BPI, Unionbank, etc. (1-2 business days)", tl: "BDO, BPI, Unionbank, etc. (1-2 araw)" },
  "cashout.continue": { en: "Continue", tl: "Continue" },
  "cashout.confirm": { en: "Confirm Cash Out", tl: "Confirm na Cash Out" },
  "cashout.fee": { en: "Fee", tl: "Fee" },
  "cashout.free": { en: "FREE", tl: "LIBRE" },
  "cashout.confirm_btn": { en: "Confirm Transfer", tl: "I-confirm" },
  "cashout.success_title": { en: "Transfer Initiated", tl: "Nai-transfer na" },

  // Feed
  "feed.title": { en: "Scholarship Feed", tl: "Scholarship Feed" },
  "feed.subtitle": { en: "Scholarships recommended by fellow students", tl: "Mga scholarship na ni-recommend ng mga ka-estudyante" },

  // Login
  "login.title": { en: "Sign in", tl: "Sign in" },
  "login.subtitle": { en: "Connect wallet and access Merit", tl: "I-connect ang wallet at i-access ang Merit" },
  "login.connect_wallet": { en: "Connect Wallet", tl: "Connect Wallet" },
  "login.connect_freighter": { en: "Connect Freighter", tl: "I-connect ang Freighter" },
  "login.connected": { en: "Connected", tl: "Connected na" },
  "login.sign_in": { en: "Sign in", tl: "Sign in" },
  "login.student_demo": { en: "Student Demo", tl: "Student Demo" },
  "login.admin_demo": { en: "Admin Demo", tl: "Admin Demo" },
  "login.new_to_merit": { en: "New to Merit?", tl: "Bago ka sa Merit?" },
  "login.create_account": { en: "Create an account", tl: "Gumawa ng account" },

  // Onboarding
  "onboard.skip": { en: "Skip", tl: "Skip" },
  "onboard.continue": { en: "Continue", tl: "Next" },
  "onboard.get_started": { en: "Get Started", tl: "Tara na" },

  // Transactions
  "tx.title": { en: "Transactions", tl: "Transactions" },
  "tx.subtitle": { en: "Complete history of your scholarship activity", tl: "Buong history ng scholarship activity mo" },
  "tx.all": { en: "All", tl: "Lahat" },
  "tx.applications": { en: "Applications", tl: "Applications" },
  "tx.disbursements": { en: "Disbursements", tl: "Disbursements" },
  "tx.withdrawals": { en: "Withdrawals", tl: "Withdrawals" },

  // Wallet
  "wallet.title": { en: "Wallet", tl: "Wallet" },
  "wallet.subtitle": { en: "Your Stellar wallet on testnet", tl: "Ang Stellar wallet mo sa testnet" },
  "wallet.balance": { en: "Balance", tl: "Balance" },
  "wallet.transactions": { en: "Transactions", tl: "Transactions" },

  // General
  "general.back": { en: "Back", tl: "Back" },
  "general.cancel": { en: "Cancel", tl: "Cancel" },
};

interface LangContextType {
  lang: Lang;
  setLang: (l: Lang) => void;
  text: (key: string) => string;
}

const LangContext = createContext<LangContextType>({ lang: "en", setLang: () => {}, text: (k) => k });

export function useLang() {
  return useContext(LangContext);
}

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("merit_lang") as Lang | null;
    if (stored === "en" || stored === "tl") {
      setLangState(stored);
    }
    setMounted(true);
  }, []);

  const setLang = (l: Lang) => {
    setLangState(l);
    localStorage.setItem("merit_lang", l);
  };

  const text = (key: string): string => {
    const entry = t[key];
    if (!entry) return key;
    return entry[lang] || entry.en || key;
  };

  if (!mounted) return <>{children}</>;

  return (
    <LangContext.Provider value={{ lang, setLang, text }}>
      {children}
    </LangContext.Provider>
  );
}

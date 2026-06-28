"use client";

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";

export type Lang = "en" | "tl";

// All site translations
const translations: Record<string, Record<Lang, string>> = {
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
  "dash.save": { en: "Save", tl: "Mag-ipon" },
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
  "savings.title": { en: "Savings Goals", tl: "Mga Savings Goal" },
  "savings.subtitle": { en: "Set it, lock it, reach it.", tl: "I-set, i-lock, abutin." },
  "savings.new_goal": { en: "New Goal", tl: "Bagong Goal" },
  "savings.total_saved": { en: "Total Saved", tl: "Kabuuang Na-ipon" },
  "savings.create_goal": { en: "Create Savings Goal", tl: "Gumawa ng Savings Goal" },
  "savings.what_saving": { en: "What are you saving for?", tl: "Para saan ang iipon mo?" },
  "savings.target_amount": { en: "Target Amount (PHP)", tl: "Target na Halaga (PHP)" },
  "savings.locked_info": { en: "Funds locked in this goal cannot be withdrawn until the target is reached.", tl: "Hindi mo pwede i-withdraw hanggang di mo pa naabot ang target." },
  "savings.create": { en: "Create Goal", tl: "Gumawa na" },
  "savings.reached": { en: "reached", tl: "naabot na" },
  "savings.locked": { en: "Locked until target", tl: "Naka-lock hanggang maabot" },
  "savings.ready": { en: "Ready to withdraw", tl: "Pwede na i-withdraw" },
  "savings.started": { en: "Started", tl: "Nagsimula" },

  // Cash Out
  "cashout.title": { en: "Cash Out", tl: "Cash Out" },
  "cashout.subtitle": { en: "Transfer funds to your account — zero fees", tl: "I-transfer sa account mo — walang bayad" },
  "cashout.no_fee": { en: "No transaction fees. Your full scholarship amount goes to you.", tl: "Walang transaction fee. Buong scholarship mo mapupunta sa'yo." },
  "cashout.select_method": { en: "Select cash out method", tl: "Pumili ng paraan" },
  "cashout.continue": { en: "Continue", tl: "Magpatuloy" },
  "cashout.confirm": { en: "Confirm Cash Out", tl: "Kumpirmahin ang Cash Out" },
  "cashout.fee": { en: "Fee", tl: "Bayad" },
  "cashout.free": { en: "FREE", tl: "LIBRE" },
  "cashout.confirm_btn": { en: "Confirm Transfer", tl: "Kumpirmahin" },
  "cashout.success_title": { en: "Transfer Initiated", tl: "Naisumite na ang Transfer" },
  "cashout.back": { en: "Back", tl: "Bumalik" },

  // Feed
  "feed.title": { en: "Scholarship Feed", tl: "Scholarship Feed" },
  "feed.subtitle": { en: "Scholarships recommended by fellow students", tl: "Mga scholarship na nirerekomenda ng mga kapwa estudyante" },
  "feed.share": { en: "Share", tl: "Ibahagi" },
  "feed.all": { en: "All", tl: "Lahat" },
  "feed.national": { en: "National", tl: "National" },
  "feed.city": { en: "City", tl: "Lokal" },

  // Login
  "login.title": { en: "Sign in", tl: "Mag-sign in" },
  "login.subtitle": { en: "Connect wallet and access Merit", tl: "I-connect ang wallet at i-access ang Merit" },
  "login.connect_wallet": { en: "Connect Wallet", tl: "I-connect ang Wallet" },
  "login.connect_freighter": { en: "Connect Freighter", tl: "I-connect ang Freighter" },
  "login.connected": { en: "Connected", tl: "Naka-connect na" },
  "login.sign_in": { en: "Sign in", tl: "Mag-sign in" },
  "login.student_demo": { en: "Student Demo", tl: "Student Demo" },
  "login.admin_demo": { en: "Admin Demo", tl: "Admin Demo" },
  "login.new_to_merit": { en: "New to Merit?", tl: "Bago ka sa Merit?" },
  "login.create_account": { en: "Create an account", tl: "Gumawa ng account" },
  "login.email": { en: "Email", tl: "Email" },
  "login.password": { en: "Password", tl: "Password" },
  "login.forgot": { en: "Forgot?", tl: "Nakalimutan?" },
  "login.install_freighter": { en: "Install Freighter", tl: "I-install ang Freighter" },
  "login.browser_ext": { en: "Browser extension required", tl: "Kailangan ng browser extension" },

  // Onboarding
  "onboard.skip": { en: "Skip", tl: "Laktawan" },
  "onboard.continue": { en: "Continue", tl: "Susunod" },
  "onboard.get_started": { en: "Get Started", tl: "Magsimula na" },

  // Transactions
  "tx.title": { en: "Transactions", tl: "Mga Transaksyon" },
  "tx.subtitle": { en: "Complete history of your scholarship activity", tl: "Buong history ng scholarship activity mo" },
  "tx.all": { en: "All", tl: "Lahat" },
  "tx.applications": { en: "Applications", tl: "Mga Application" },
  "tx.disbursements": { en: "Disbursements", tl: "Mga Natanggap" },
  "tx.withdrawals": { en: "Withdrawals", tl: "Mga Na-withdraw" },

  // Wallet
  "wallet.title": { en: "Wallet", tl: "Wallet" },
  "wallet.subtitle": { en: "Your Stellar wallet on testnet", tl: "Ang Stellar wallet mo sa testnet" },
  "wallet.balance": { en: "Balance", tl: "Balanse" },
  "wallet.transactions": { en: "Transactions", tl: "Mga Transaksyon" },
  "wallet.no_transactions": { en: "No transactions yet", tl: "Wala pang transaksyon" },

  // Notifications
  "notif.title": { en: "Notifications", tl: "Mga Abiso" },
  "notif.unread": { en: "unread", tl: "hindi pa nabasa" },

  // General
  "general.back": { en: "Back", tl: "Bumalik" },
  "general.cancel": { en: "Cancel", tl: "Kanselahin" },
};

interface LangContextType {
  lang: Lang;
  setLang: (l: Lang) => void;
  text: (key: string) => string;
}

const LangContext = createContext<LangContextType>({
  lang: "en",
  setLang: () => {},
  text: (k) => k,
});

export function useLang() {
  return useContext(LangContext);
}

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");

  // Read from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem("merit_lang") as Lang | null;
    if (stored === "en" || stored === "tl") {
      setLangState(stored);
    }
  }, []);

  // Listen for changes from the dropdown (which triggers reload, but just in case)
  useEffect(() => {
    function onStorage() {
      const stored = localStorage.getItem("merit_lang") as Lang | null;
      if (stored && stored !== lang) setLangState(stored);
    }
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [lang]);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    localStorage.setItem("merit_lang", l);
  }, []);

  const text = useCallback((key: string): string => {
    const entry = translations[key];
    if (!entry) return key;
    return entry[lang] || entry["en"] || key;
  }, [lang]);

  return (
    <LangContext.Provider value={{ lang, setLang, text }}>
      {children}
    </LangContext.Provider>
  );
}

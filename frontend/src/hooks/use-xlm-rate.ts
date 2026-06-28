"use client";

import { useState, useEffect, useCallback } from "react";

/**
 * Hook that fetches the real-time XLM/PHP exchange rate from CoinGecko API.
 * Falls back to a cached/default rate if the API is unavailable.
 */

const CACHE_KEY = "merit_xlm_php_rate";
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

interface CachedRate {
  rate: number;
  timestamp: number;
}

function getCachedRate(): number | null {
  if (typeof window === "undefined") return null;
  const cached = localStorage.getItem(CACHE_KEY);
  if (!cached) return null;
  try {
    const parsed: CachedRate = JSON.parse(cached);
    if (Date.now() - parsed.timestamp < CACHE_DURATION) {
      return parsed.rate;
    }
  } catch {}
  return null;
}

function setCachedRate(rate: number) {
  if (typeof window === "undefined") return;
  localStorage.setItem(CACHE_KEY, JSON.stringify({ rate, timestamp: Date.now() }));
}

export function useXlmRate() {
  // Default fallback rate (approximate XLM/PHP as of mid-2026)
  const [rate, setRate] = useState<number>(getCachedRate() || 17.5);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const fetchRate = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(
        "https://api.coingecko.com/api/v3/simple/price?ids=stellar&vs_currencies=php"
      );
      if (response.ok) {
        const data = await response.json();
        const phpRate = data?.stellar?.php;
        if (phpRate && typeof phpRate === "number") {
          setRate(phpRate);
          setCachedRate(phpRate);
          setLastUpdated(new Date().toLocaleTimeString());
        }
      }
    } catch {
      // Use cached or fallback
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRate();
    // Refresh every 5 minutes
    const interval = setInterval(fetchRate, CACHE_DURATION);
    return () => clearInterval(interval);
  }, [fetchRate]);

  return { rate, loading, lastUpdated, refetch: fetchRate };
}

/**
 * Convert PHP to XLM
 */
export function phpToXlm(php: number, rate: number): number {
  if (rate <= 0) return 0;
  return php / rate;
}

/**
 * Convert XLM to PHP
 */
export function xlmToPhp(xlm: number, rate: number): number {
  return xlm * rate;
}

/**
 * Format currency display
 */
export function formatCurrency(amount: number, currency: "PHP" | "XLM"): string {
  if (currency === "PHP") {
    return `PHP ${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return `${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })} XLM`;
}

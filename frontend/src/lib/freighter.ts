"use client";

/**
 * Freighter wallet integration utilities.
 * Handles connection, public key retrieval, and network checks.
 */

import { isConnected, requestAccess, getAddress, getNetwork } from "@stellar/freighter-api";

const FREIGHTER_KEY = "merit_freighter_pubkey";

export interface FreighterState {
  connected: boolean;
  publicKey: string | null;
  network: string | null;
}

/**
 * Check if Freighter extension is installed in the browser.
 */
export async function isFreighterInstalled(): Promise<boolean> {
  try {
    const result = await isConnected();
    return result.isConnected;
  } catch {
    return false;
  }
}

/**
 * Request Freighter wallet connection (opens the Freighter popup).
 * Returns the public key on success.
 */
export async function connectFreighter(): Promise<string | null> {
  try {
    const accessResult = await requestAccess();
    if (accessResult.error) {
      console.error("Freighter access denied:", accessResult.error);
      return null;
    }

    const addressResult = await getAddress();
    if (addressResult.error) {
      console.error("Failed to get address:", addressResult.error);
      return null;
    }

    const pubKey = addressResult.address;

    // Store in localStorage for persistence
    if (typeof window !== "undefined" && pubKey) {
      localStorage.setItem(FREIGHTER_KEY, pubKey);
    }

    return pubKey;
  } catch (err) {
    console.error("Freighter connection error:", err);
    return null;
  }
}

/**
 * Get the currently connected Freighter public key (from cache or fresh).
 */
export async function getFreighterPublicKey(): Promise<string | null> {
  try {
    const addressResult = await getAddress();
    if (addressResult.error || !addressResult.address) {
      return getCachedPublicKey();
    }
    return addressResult.address;
  } catch {
    return getCachedPublicKey();
  }
}

/**
 * Get cached public key from localStorage.
 */
export function getCachedPublicKey(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(FREIGHTER_KEY);
}

/**
 * Get the connected Stellar network from Freighter.
 */
export async function getFreighterNetwork(): Promise<string | null> {
  try {
    const result = await getNetwork();
    if (result.error) return null;
    return result.network;
  } catch {
    return null;
  }
}

/**
 * Disconnect wallet (clear local state).
 */
export function disconnectFreighter(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(FREIGHTER_KEY);
  }
}

/**
 * Check full Freighter state.
 */
export async function getFreighterState(): Promise<FreighterState> {
  const installed = await isFreighterInstalled();
  if (!installed) {
    return { connected: false, publicKey: null, network: null };
  }

  const publicKey = await getFreighterPublicKey();
  const network = publicKey ? await getFreighterNetwork() : null;

  return {
    connected: !!publicKey,
    publicKey,
    network,
  };
}

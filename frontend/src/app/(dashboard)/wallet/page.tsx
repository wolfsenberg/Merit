"use client";

import { useWallet, useCreateWallet, useTransactions } from "@/hooks/use-api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function WalletPage() {
  const { data: wallet, isLoading, error } = useWallet();
  const createWallet = useCreateWallet();
  const { data: transactions } = useTransactions();

  if (isLoading) return <div className="flex justify-center p-8"><div className="h-8 w-8 animate-spin rounded-full border-4 border-gold-500 border-t-transparent" /></div>;

  if (error || !wallet) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Wallet</h1>
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground mb-4">You don&apos;t have a wallet yet.</p>
            <Button onClick={() => createWallet.mutate()} className="bg-gold-500 hover:bg-gold-600" disabled={createWallet.isPending}>
              {createWallet.isPending ? "Creating..." : "Create Wallet"}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Wallet</h1>
      <Card>
        <CardHeader><CardTitle>Stellar Wallet</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-muted-foreground">Public Key</p>
          <p className="font-mono text-sm break-all">{wallet.public_key}</p>
          <p className="text-sm text-muted-foreground mt-4">Network: {wallet.network}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Transaction History</CardTitle></CardHeader>
        <CardContent>
          {transactions?.items.length === 0 ? (
            <p className="text-muted-foreground text-center py-4">No transactions yet</p>
          ) : (
            <div className="space-y-2">
              {transactions?.items.map((tx) => (
                <div key={tx.id} className="flex justify-between items-center border-b pb-2">
                  <div>
                    <p className="text-sm font-medium">{tx.status === "confirmed" ? "Received" : tx.status}</p>
                    <p className="text-xs text-muted-foreground">{new Date(tx.created_at).toLocaleDateString()}</p>
                  </div>
                  <p className="font-medium text-green-600">+{tx.amount} {tx.asset_code}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

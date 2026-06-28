import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { MobilePreviewWrapper } from "@/components/layout/mobile-preview";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Merit Platform",
  description: "AI-assisted conditional funding platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <MobilePreviewWrapper>
            {children}
          </MobilePreviewWrapper>
        </Providers>
      </body>
    </html>
  );
}

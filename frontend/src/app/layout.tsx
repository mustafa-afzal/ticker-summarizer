import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PitchSheet Agent",
  description: "Convert SEC filings into pitch-ready Excel models",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <nav className="border-b border-slate-200 bg-white">
          <div className="mx-auto max-w-5xl px-6 py-4 flex items-center justify-between">
            <Link href="/" className="text-xl font-bold text-blue-800 hover:text-blue-900">
              PitchSheet Agent
            </Link>
            <div className="flex gap-6 text-sm font-medium">
              <Link href="/" className="text-slate-600 hover:text-blue-700">
                New Model
              </Link>
              <Link href="/history" className="text-slate-600 hover:text-blue-700">
                History
              </Link>
            </div>
          </div>
        </nav>
        <main className="mx-auto max-w-5xl px-6 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IPL 2026 Fantasy Predictor",
  description: "Who's winning the fantasy draft? AI-powered predictions for your IPL 2026 fantasy league.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-gray-950 text-white font-sans">{children}</body>
    </html>
  );
}

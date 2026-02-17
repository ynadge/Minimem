import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MiniMem — Organizational Memory Demo",
  description: "AI-powered organizational alignment checker",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

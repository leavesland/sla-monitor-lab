import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SLA Monitor",
  description: "Uptime and latency for a list of URLs, checked by background workers.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Weaver",
  description: "Weave knowledge into insights. AI-powered research workspace with infinite canvas.",
  icons: {
    icon: "/weaver-logo.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}

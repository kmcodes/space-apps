import type { Metadata, Viewport } from "next";
import { Anek_Devanagari } from "next/font/google";
import "./globals.css";

// One family with Latin and Devanagari, so English, Hindi and Marathi share a look.
// The width axis gives the narrow cut used for headings and figures.
const anek = Anek_Devanagari({
  subsets: ["latin", "devanagari"],
  axes: ["wdth"],
  variable: "--font-anek",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Field Shift",
  description: "Compare crop rotations for rainfed farms in Vidarbha, with NASA evidence and the unknowns for each.",
};

export const viewport: Viewport = {
  themeColor: "#2b2320",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${anek.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">{children}</body>
    </html>
  );
}

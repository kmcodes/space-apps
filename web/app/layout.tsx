import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Field Shift",
  description: "Compare crop rotations for rainfed farms in Vidarbha, with NASA evidence and the unknowns for each.",
};

export const viewport: Viewport = {
  themeColor: "#065f46",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex min-h-full flex-col">{children}</body>
    </html>
  );
}

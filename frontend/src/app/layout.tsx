/**
 * Root Layout
 * Sets up global fonts, metadata, and the base HTML shell.
 */
import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default:  "Architect",
    template: "%s | Architect",
  },
  description:
    "An AI-powered orchestration platform that transforms naive ideas into professional engineering implementations.",
  keywords: ["AI", "engineering", "orchestration", "LangGraph", "FastAPI"],
};

export const viewport: Viewport = {
  themeColor: "#080c14",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head />
      <body className="antialiased">{children}</body>
    </html>
  );
}
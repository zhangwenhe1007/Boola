import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Boola - Yale AI Assistant",
  description:
    "Your AI assistant for all things Yale. Ask about courses, clubs, deadlines, campus resources, and more.",
  keywords: ["Yale", "AI", "assistant", "courses", "campus", "students"],
  authors: [{ name: "Boola Team" }],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#00356b",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
